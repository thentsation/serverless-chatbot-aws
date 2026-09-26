🇧🇷 Português | [🇺🇸 English](ARTIGO.en-us.md)

# Uma função que nunca existiu, chamada em produção

Esse é um projeto sério — AppSync, Bedrock, Lambda em container, Cognito, DynamoDB, tudo via Terraform modular, com um README que já documentava a arquitetura inteira antes de eu tocar em qualquer coisa. Não existia CI nenhum. E existia um bug que só se manifestaria numa execução específica: `NameError: name 'add_assistant_message' is not defined`.

## O bug: uma função renomeada pela metade

```python
# original
def save_assistant_message(chat_id, content):
    ...

def handler(event, _ctx):
    if event.get("action") == "trigger_subscription":
        ...
        result = add_assistant_message(     # <- essa função não existe
            assistant_message["chatId"],
            assistant_message["userId"],    # <- e a mutation nem aceita userId
            assistant_message["content"]
        )
```

A função que salva a mensagem do assistente se chama `save_assistant_message` e recebe dois argumentos (`chat_id`, `content`) — batendo exatamente com a mutation GraphQL `addAssistantMessage(chatId: ID!, content: String!)` do schema. O branch `trigger_subscription` do handler, só usado quando algo dispara a subscription manualmente (não no fluxo principal de chat), chamava uma função de nome parecido que nunca existiu, com um terceiro argumento (`userId`) que a mutation nem aceita. Esse caminho de código simplesmente nunca tinha sido exercitado — nem por um teste, nem por um uso real recente — e por isso o `NameError` nunca apareceu.

A correção foi trivial depois de identificado: chamar a função que já existe, com a assinatura certa.

## O segredo que ia parar no CloudWatch

```python
def sign_and_post(url, payload: dict):
    try:
        print(f"Environment APPSYNC_API_KEY: {repr(APPSYNC_API_KEY)}")
```

Essa linha imprimia a **API key da AppSync, em texto puro**, em todo request — e no Lambda, `print()` vai direto pro CloudWatch Logs. Qualquer pessoa com acesso de leitura aos logs (um escopo de permissão bem mais comum do que acesso à Secrets Manager ou ao Terraform state) conseguiria extrair a chave e chamar a API diretamente. Removi essa linha e as outras que ecoavam `Using API Key: {bool(...)}` continuam — não vazam o segredo, só confirmam que ele está configurado.

## Testando um handler de Lambda sem AWS de verdade

Todas as chamadas de rede (`urlreq.urlopen` para a AppSync, `boto3.client("bedrock-runtime")` para o Bedrock) são mockadas nos testes — não porque sejam caras, mas porque **não existem** num ambiente de CI sem credenciais reais da AWS. 23 testes cobrem os três formatos de payload do Bedrock (Claude, Nova, Titan), a assinatura SigV4 quando não há API key, cada branch de validação do handler, e o bug do `add_assistant_message` especificamente (o teste `test_handler_trigger_subscription_calls_save_assistant_message` chama exatamente esse caminho e falharia com o código original).

## O que o CI faz — e o que ele nunca vai fazer

Este repositório provisiona infraestrutura real via `terraform apply`. Eu não tenho, e não deveria ter, credenciais para isso, e nenhum pipeline automático deveria rodar `apply`/`destroy` sem um humano decidindo explicitamente. O CI de Terraform faz só `terraform fmt -check` e `terraform validate` com `init -backend=false` — verificação estática, sem tocar em nenhuma credencial ou state real — mais um scan de segurança com `tfsec`. Rodei os dois localmente antes de configurar o pipeline: `fmt` encontrou formatação inconsistente em cinco arquivos (espaços alinhados manualmente, blocos vazios) que corrigi com `terraform fmt -recursive`; `validate` passou, com um aviso pré-existente e não relacionado (`range_key` deprecated em `aws_dynamodb_table`) que não mexi, por não ser meu lugar alterar o schema de uma tabela DynamoDB que pode já ter dados reais.

O pipeline Docker builda a imagem do Lambda (`infra/lambdas/orchestrator`) e escaneia com Trivy — mas não publica em lugar nenhum. Não existe GHCR fazendo sentido aqui (a imagem vai pro ECR, via `docker-upload.sh`, manual, com credenciais da AWS do usuário) e automatizar esse push exigiria eu ter acesso à conta AWS de produção, o que não é o caso nem deveria ser.
