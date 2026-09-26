import json
from unittest.mock import MagicMock, patch

import app
import pytest


def _mock_urlopen(response_json: dict):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(response_json).encode()
    return cm


def test_sign_and_post_uses_api_key_header_when_present() -> None:
    with patch(
        "app.urlreq.urlopen", return_value=_mock_urlopen({"data": {"ok": True}})
    ):
        result = app.sign_and_post(app.APPSYNC_URL, {"query": "query"})
    assert result == {"ok": True}


def test_sign_and_post_raises_on_graphql_errors() -> None:
    with (
        patch(
            "app.urlreq.urlopen",
            return_value=_mock_urlopen({"errors": [{"message": "boom"}]}),
        ),
        pytest.raises(RuntimeError, match="boom"),
    ):
        app.sign_and_post(app.APPSYNC_URL, {"query": "query"})


def test_sign_and_post_signs_with_sigv4_when_no_api_key(monkeypatch) -> None:
    monkeypatch.setattr(app, "APPSYNC_API_KEY", "")
    fake_credentials = MagicMock()
    fake_session = MagicMock()
    fake_session.get_credentials.return_value = fake_credentials

    with (
        patch("app.boto3.Session", return_value=fake_session),
        patch("app.SigV4Auth"),
        patch("app.urlreq.urlopen", return_value=_mock_urlopen({"data": {"ok": True}})),
    ):
        result = app.sign_and_post(app.APPSYNC_URL, {"query": "query"})

    assert result == {"ok": True}


def test_sign_and_post_raises_without_credentials(monkeypatch) -> None:
    monkeypatch.setattr(app, "APPSYNC_API_KEY", "")
    fake_session = MagicMock()
    fake_session.get_credentials.return_value = None

    with (
        patch("app.boto3.Session", return_value=fake_session),
        pytest.raises(RuntimeError, match="No AWS credentials"),
    ):
        app.sign_and_post(app.APPSYNC_URL, {"query": "query"})


def test_sign_and_post_reraises_network_errors() -> None:
    with (
        patch("app.urlreq.urlopen", side_effect=TimeoutError("timed out")),
        pytest.raises(TimeoutError),
    ):
        app.sign_and_post(app.APPSYNC_URL, {"query": "query"})


def test_get_chat_history_maps_role_and_content() -> None:
    graphql_response = {
        "data": {
            "listMessages": {
                "items": [
                    {"role": "user", "content": "hi", "createdAt": "t1"},
                    {"role": "assistant", "content": "hello", "createdAt": "t2"},
                ]
            }
        }
    }
    with patch("app.urlreq.urlopen", return_value=_mock_urlopen(graphql_response)):
        history = app.get_chat_history("chat-1")

    assert history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_save_assistant_message_returns_created_message() -> None:
    graphql_response = {"data": {"addAssistantMessage": {"id": "m1", "content": "hi"}}}
    with patch("app.urlreq.urlopen", return_value=_mock_urlopen(graphql_response)):
        result = app.save_assistant_message("chat-1", "hi")

    assert result == {"id": "m1", "content": "hi"}


def test_bedrock_request_body_claude() -> None:
    body = app._bedrock_request_body(
        "anthropic.claude-3",
        [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
    )
    assert body["system"] == "sys"
    assert body["messages"] == [{"role": "user", "content": [{"text": "hi"}]}]


def test_bedrock_request_body_nova() -> None:
    body = app._bedrock_request_body(
        "amazon.nova-micro-v1:0", [{"role": "user", "content": "hi"}]
    )
    assert body["messages"] == [{"role": "user", "content": [{"text": "hi"}]}]


def test_bedrock_request_body_titan() -> None:
    body = app._bedrock_request_body(
        "amazon.titan-text", [{"role": "user", "content": "hi"}]
    )
    assert "Human: hi" in body["inputText"]


def test_bedrock_request_body_unknown_model_raises() -> None:
    with pytest.raises(ValueError, match="não suportado"):
        app._bedrock_request_body("some.other-model", [])


def test_bedrock_response_text_claude_and_titan_and_unknown() -> None:
    assert (
        app._bedrock_response_text("anthropic.claude-3", {"content": [{"text": "hi"}]})
        == "hi"
    )
    assert (
        app._bedrock_response_text(
            "amazon.titan-text", {"results": [{"outputText": "hi "}]}
        )
        == "hi"
    )
    assert app._bedrock_response_text("amazon.titan-text", {"results": []}) is None


def test_call_bedrock_returns_friendly_message_on_error() -> None:
    with patch("app.boto3.client", side_effect=RuntimeError("boto3 down")):
        reply = app.call_bedrock([{"role": "user", "content": "hi"}])

    assert "Erro ao processar" in reply


def test_call_bedrock_invokes_the_right_model_and_parses_nova_output() -> None:
    fake_client = MagicMock()
    fake_client.invoke_model.return_value = {
        "body": MagicMock(
            read=lambda: json.dumps(
                {"output": {"message": {"content": [{"text": "oi!"}]}}}
            ).encode()
        )
    }
    with patch("app.boto3.client", return_value=fake_client):
        reply = app.call_bedrock([{"role": "user", "content": "hi"}])

    assert reply == "oi!"
    fake_client.invoke_model.assert_called_once()


def test_handler_trigger_subscription_calls_save_assistant_message() -> None:
    event = {
        "action": "trigger_subscription",
        "assistantMessage": {"chatId": "c1", "userId": "u1", "content": "hi"},
    }
    with patch("app.save_assistant_message", return_value={"id": "m1"}) as save:
        result = app.handler(event, None)

    save.assert_called_once_with("c1", "hi")
    assert result == {
        "success": True,
        "triggeredSubscription": True,
        "result": {"id": "m1"},
    }


def test_handler_skip_action() -> None:
    assert app.handler({"action": "skip"}, None) == {"success": True, "skipped": True}


def test_handler_full_flow() -> None:
    event = {
        "arguments": {"chatId": "c1", "content": "hi"},
        "identity": {"sub": "u1"},
    }
    with (
        patch("app.get_chat_history", return_value=[]),
        patch("app.call_bedrock", return_value="oi"),
        patch("app.save_assistant_message", return_value={"id": "m1"}) as save,
    ):
        result = app.handler(event, None)

    save.assert_called_once_with("c1", "oi")
    assert result["success"] is True
    assert result["assistantMessage"]["content"] == "oi"


def test_handler_missing_chat_id_returns_error() -> None:
    event = {"arguments": {"content": "hi"}, "identity": {"sub": "u1"}}
    result = app.handler(event, None)
    assert result["success"] is False
    assert "chatId" in result["error"]


def test_handler_missing_content_returns_error() -> None:
    event = {"arguments": {"chatId": "c1"}, "identity": {"sub": "u1"}}
    result = app.handler(event, None)
    assert "content" in result["error"]


def test_handler_missing_user_id_returns_error() -> None:
    event = {"arguments": {"chatId": "c1", "content": "hi"}, "identity": {}}
    result = app.handler(event, None)
    assert "User ID" in result["error"]


def test_handler_trigger_subscription_without_message() -> None:
    result = app.handler({"action": "trigger_subscription"}, None)
    assert result == {
        "success": False,
        "error": "Nenhuma mensagem do assistant fornecida",
    }


def test_handler_trigger_subscription_error_is_caught() -> None:
    event = {
        "action": "trigger_subscription",
        "assistantMessage": {"chatId": "c1", "content": "hi"},
    }
    with patch("app.save_assistant_message", side_effect=RuntimeError("down")):
        result = app.handler(event, None)
    assert result == {"success": False, "error": "down"}


def test_handler_generic_exception_is_caught() -> None:
    event = {"arguments": {"chatId": "c1", "content": "hi"}, "identity": {"sub": "u1"}}
    with patch("app.get_chat_history", side_effect=RuntimeError("down")):
        result = app.handler(event, None)
    assert result["success"] is False
    assert "down" in result["error"]
