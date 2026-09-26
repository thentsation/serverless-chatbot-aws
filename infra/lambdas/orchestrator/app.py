import json
import os
from typing import Any
from urllib import request as urlreq

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

APPSYNC_URL = os.environ["APPSYNC_URL"]
APPSYNC_API_KEY = os.environ.get("APPSYNC_API_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL", "amazon.nova-micro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")


def sign_and_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    if APPSYNC_API_KEY:
        headers["x-api-key"] = APPSYNC_API_KEY
        request = urlreq.Request(url, data=data, method="POST", headers=headers)
    else:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            raise RuntimeError("No AWS credentials available")

        aws_request = AWSRequest(method="POST", url=url, data=data, headers=headers)
        SigV4Auth(credentials, "appsync", AWS_REGION).add_auth(aws_request)

        request = urlreq.Request(url, data=data, method="POST")
        for header_name, header_value in aws_request.headers.items():
            request.add_header(header_name, header_value)

    try:
        with urlreq.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception:
        print(f"Error calling AppSync at {url}")
        raise

    if "errors" in result:
        print(f"GraphQL errors: {result['errors']}")
        raise RuntimeError(f"GraphQL errors: {result['errors']}")

    return result.get("data", result)


def _bedrock_request_body(model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    is_claude = "anthropic" in model.lower()
    is_titan = "amazon.titan" in model.lower()
    is_nova = "amazon.nova" in model.lower()

    if is_claude or is_nova:
        conversation = []
        system_message = ""
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation.append(
                    {"role": msg["role"], "content": [{"text": msg["content"]}]}
                )

        if is_claude:
            body: dict[str, Any] = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.4,
                "messages": conversation,
            }
            if system_message:
                body["system"] = system_message
            return body

        body = {
            "messages": conversation,
            "inferenceConfig": {
                "max_new_tokens": 4000,
                "temperature": 0.4,
                "top_p": 0.9,
            },
        }
        if system_message:
            body["system"] = [{"text": system_message}]
        return body

    if is_titan:
        prompt_text = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt_text += f"System: {msg['content']}\n\n"
            elif msg["role"] == "user":
                prompt_text += f"Human: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt_text += f"Assistant: {msg['content']}\n\n"
        prompt_text += "Assistant:"
        return {
            "inputText": prompt_text,
            "textGenerationConfig": {
                "maxTokenCount": 4000,
                "temperature": 0.4,
                "topP": 0.9,
                "stopSequences": ["Human:", "System:"],
            },
        }

    raise ValueError(f"Modelo não suportado: {model}")


def _bedrock_response_text(model: str, response_body: dict[str, Any]) -> str | None:
    if "anthropic" in model.lower():
        content = response_body.get("content")
        if content:
            return str(content[0]["text"])
    elif "amazon.nova" in model.lower():
        output = response_body.get("output", {})
        message = output.get("message")
        if message:
            return str(message["content"][0]["text"])
    elif "amazon.titan" in model.lower():
        results = response_body.get("results")
        if results:
            return str(results[0]["outputText"].strip())
    return None


def call_bedrock(messages: list[dict[str, str]]) -> str:
    try:
        bedrock_runtime = boto3.client(
            service_name="bedrock-runtime", region_name=BEDROCK_REGION
        )
        request_body = _bedrock_request_body(BEDROCK_MODEL, messages)

        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL, body=json.dumps(request_body)
        )
        response_body = json.loads(response["body"].read())

        return (
            _bedrock_response_text(BEDROCK_MODEL, response_body)
            or "Desculpe, não consegui gerar uma resposta."
        )
    except Exception as e:
        print(f"Erro ao chamar Bedrock: {e}")
        return f"Erro ao processar sua solicitação: {e}"


def get_chat_history(chat_id: str) -> list[dict[str, str]]:
    query = """
      query GetMessages($chatId: ID!, $limit: Int) {
        listMessages(chatId: $chatId, limit: $limit) {
          items {
            role
            content
            createdAt
          }
        }
      }
    """

    result = sign_and_post(
        APPSYNC_URL, {"query": query, "variables": {"chatId": chat_id, "limit": 50}}
    )

    messages = result.get("listMessages", {}).get("items", [])
    return [{"role": msg["role"], "content": msg["content"]} for msg in messages]


def save_assistant_message(chat_id: str, content: str) -> dict[str, Any] | None:
    mutation = """
      mutation AddAssistant($chatId: ID!, $content: String!) {
        addAssistantMessage(chatId: $chatId, content: $content) {
          id
          chatId
          userId
          role
          content
          createdAt
        }
      }
    """

    result = sign_and_post(
        APPSYNC_URL,
        {"query": mutation, "variables": {"chatId": chat_id, "content": content}},
    )

    return result.get("addAssistantMessage")


def _handle_trigger_subscription(event: dict[str, Any]) -> dict[str, Any]:
    assistant_message = event.get("assistantMessage")
    if not assistant_message:
        return {"success": False, "error": "Nenhuma mensagem do assistant fornecida"}

    try:
        result = save_assistant_message(
            assistant_message["chatId"], assistant_message["content"]
        )
        return {"success": True, "triggeredSubscription": True, "result": result}
    except Exception as e:
        print(f"Erro ao triggerar subscription: {e}")
        return {"success": False, "error": str(e)}


def handler(event: dict[str, Any], _ctx: Any) -> dict[str, Any]:
    if event.get("action") == "trigger_subscription":
        return _handle_trigger_subscription(event)

    if event.get("action") == "skip":
        return {"success": True, "skipped": True}

    try:
        args = event.get("arguments", {})
        identity = event.get("identity", {})

        chat_id = args.get("chatId")
        user_input = args.get("content")
        user_id = identity.get("sub")

        if not chat_id:
            raise ValueError("chatId é obrigatório")
        if not user_input:
            raise ValueError("content é obrigatório")
        if not user_id:
            raise ValueError("User ID é obrigatório para autenticação")

        history = get_chat_history(chat_id)
        history.append({"role": "user", "content": user_input})

        assistant_reply = call_bedrock(history)
        save_assistant_message(chat_id, assistant_reply)

        return {
            "success": True,
            "message": "Resposta do assistente processada com sucesso",
            "assistantMessage": {
                "chatId": chat_id,
                "userId": user_id,
                "content": assistant_reply,
            },
        }
    except Exception as e:
        error_msg = f"Erro ao processar mensagem: {e}"
        print(error_msg)
        return {"success": False, "error": error_msg}
