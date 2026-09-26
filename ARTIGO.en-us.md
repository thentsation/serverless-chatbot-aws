[🇧🇷 Português](ARTIGO.md) | 🇺🇸 English

# A function that never existed, called in production

This is a serious project — AppSync, Bedrock, containerized Lambda, Cognito, DynamoDB, all through modular Terraform, with a README that already documented the whole architecture before I touched anything. There was no CI at all. And there was a bug that would only surface on one specific code path: `NameError: name 'add_assistant_message' is not defined`.

## The bug: a function renamed halfway through

```python
# original
def save_assistant_message(chat_id, content):
    ...

def handler(event, _ctx):
    if event.get("action") == "trigger_subscription":
        ...
        result = add_assistant_message(     # <- this function doesn't exist
            assistant_message["chatId"],
            assistant_message["userId"],    # <- and the mutation doesn't take userId either
            assistant_message["content"]
        )
```

The function that saves the assistant's message is called `save_assistant_message` and takes two arguments (`chat_id`, `content`) — matching exactly the GraphQL mutation `addAssistantMessage(chatId: ID!, content: String!)` in the schema. The handler's `trigger_subscription` branch, only used when something manually triggers the subscription (not the main chat flow), called a similarly-named function that never existed, with a third argument (`userId`) the mutation doesn't even accept. This code path had simply never been exercised — not by a test, not by any recent real use — which is why the `NameError` never surfaced.

The fix was trivial once found: call the function that actually exists, with the right signature.

## The secret that was headed straight to CloudWatch

```python
def sign_and_post(url, payload: dict):
    try:
        print(f"Environment APPSYNC_API_KEY: {repr(APPSYNC_API_KEY)}")
```

This line printed the **AppSync API key, in plaintext**, on every single request — and in Lambda, `print()` goes straight to CloudWatch Logs. Anyone with read access to the logs (a far more common permission scope than access to Secrets Manager or the Terraform state) could extract the key and call the API directly. I removed this line; the other lines echoing `Using API Key: {bool(...)}` stay — they don't leak the secret, only confirm one is configured.

## Testing a Lambda handler without real AWS

Every network call (`urlreq.urlopen` to AppSync, `boto3.client("bedrock-runtime")` for Bedrock) is mocked in the tests — not because they're expensive, but because they **don't exist** in a CI environment with no real AWS credentials. 23 tests cover all three Bedrock payload formats (Claude, Nova, Titan), SigV4 signing when there's no API key, every validation branch in the handler, and the `add_assistant_message` bug specifically (`test_handler_trigger_subscription_calls_save_assistant_message` exercises exactly that path and would have failed against the original code).

## What CI does — and what it will never do

This repository provisions real infrastructure via `terraform apply`. I don't have, and shouldn't have, credentials for that, and no automated pipeline should ever run `apply`/`destroy` without a human explicitly deciding to. The Terraform CI only runs `terraform fmt -check` and `terraform validate` with `init -backend=false` — static verification, touching no real credentials or state — plus a `tfsec` security scan. I ran both locally before wiring up the pipeline: `fmt` found inconsistent formatting across five files (manually aligned spacing, empty blocks) which I fixed with `terraform fmt -recursive`; `validate` passed, with one pre-existing, unrelated warning (`range_key` deprecated on `aws_dynamodb_table`) that I left alone — it isn't my place to change a live DynamoDB table's schema shape when it may already hold real data.

The Docker pipeline builds the Lambda's image (`infra/lambdas/orchestrator`) and scans it with Trivy — but publishes it nowhere. There's no sensible GHCR target here (the image goes to ECR, via `docker-upload.sh`, manually, with the user's own AWS credentials), and automating that push would require me to have access to the production AWS account, which isn't the case and shouldn't be.
