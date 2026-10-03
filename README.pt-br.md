# Serverless Chatbot AWS

> Read in [English](README.md).

Um chatbot serverless pronto para produção, construído sobre infraestrutura AWS, usando tecnologias cloud-native modernas para experiências de IA conversacional escaláveis.

Um artigo detalhado sobre a produtização deste projeto — incluindo um bug de função inexistente no handler do Lambda e uma API key que estava sendo logada em texto puro — está disponível em [ARTIGO.md](ARTIGO.md) (pt-br) / [ARTIGO.en-us.md](ARTIGO.en-us.md) (en-us).

![Diagrama de Arquitetura](images/serverless-chatbot-aws.jpg)

## Visão geral

Este projeto implementa uma solução de chatbot totalmente serverless usando serviços AWS, desenhada para alta disponibilidade, escalabilidade e custo-benefício. A arquitetura combina subscriptions GraphQL em tempo real, conversas com IA via Amazon Bedrock, e autenticação robusta de usuários.

## Componentes da arquitetura

### Serviços principais

- **AWS AppSync**: API GraphQL com subscriptions em tempo real para comunicação bidirecional
- **Amazon Bedrock**: modelos de IA (Nova, Claude, Titan) para processamento de linguagem natural
- **AWS Lambda**: computação serverless para orquestrar os fluxos de chat
- **Amazon DynamoDB**: banco NoSQL para armazenar usuários, chats e mensagens
- **Amazon Cognito**: autenticação e autorização de usuários
- **Amazon ECR**: registro de containers para as imagens da função Lambda
- **Amazon CloudWatch**: logging e monitoramento

### Infraestrutura como código

- **Terraform**: provisionamento completo da infraestrutura, com arquitetura modular
- **Docker**: funções Lambda containerizadas para deploys consistentes

## Funcionalidades

### Funcionalidade principal

- **Gestão multi-usuário de chats**: criar, listar e deletar sessões de chat
- **Mensagens em tempo real**: comunicação bidirecional via subscriptions WebSocket
- **Respostas com IA**: integração com múltiplos modelos do Bedrock
- **Histórico de mensagens**: armazenamento e recuperação persistente de conversas
- **Autenticação de usuário**: acesso seguro via user pools do Cognito

### Capacidades técnicas

- **Múltiplos métodos de autenticação**: API Key, Cognito User Pools, AWS IAM
- **Design de banco escalável**: schema DynamoDB otimizado com GSI para queries eficientes
- **Lambda containerizada**: deploys baseados em Docker para melhor gestão de dependências
- **Subscriptions em tempo real**: subscriptions GraphQL para entrega instantânea de mensagens
- **Suporte cross-model**: compatível com Amazon Nova, Anthropic Claude e Amazon Titan

## Stack tecnológica

### Backend
- **Runtime**: Python 3.12
- **GraphQL**: AWS AppSync com resolvers em JavaScript
- **Banco de dados**: Amazon DynamoDB com chaves compostas
- **Modelos de IA**: Amazon Bedrock (Nova Micro, Claude, Titan)
- **Autenticação**: Amazon Cognito

### Infraestrutura
- **IaC**: Terraform com design modular
- **Containerização**: Docker para empacotar a Lambda
- **Monitoramento**: logs e métricas do CloudWatch
- **CI/CD**: ECR para gestão de containers

### Ferramentas de desenvolvimento
- **Scripts de teste**: clientes GraphQL em Node.js para testar a API
- **Automação de build**: Makefile para operações do Terraform
- **Gestão de ambiente**: virtual environments Python

## Estrutura do projeto

```
├── infra/                          # Componentes de infraestrutura
│   ├── terraform/                  # Módulos e configuração do Terraform
│   │   ├── modules/               # Módulos Terraform reutilizáveis
│   │   │   ├── appsync/           # Configuração da API GraphQL
│   │   │   ├── cognito/           # Autenticação de usuário
│   │   │   ├── dynamodb/          # Tabelas do banco
│   │   │   ├── lambda/            # Funções serverless
│   │   │   ├── iam/               # Políticas de controle de acesso
│   │   │   ├── ecr/               # Registro de containers
│   │   │   └── cloudwatch/        # Configuração de monitoramento
│   │   ├── main.tf                # Configuração raiz do Terraform
│   │   ├── variables.tf           # Variáveis de entrada
│   │   └── outputs.tf             # Valores de saída
│   ├── lambdas/                   # Código-fonte das funções Lambda
│   │   └── orchestrator/          # Função principal de orquestração do chat
│   │       ├── app.py             # Handler Python
│   │       └── requirements.txt   # Dependências Python
│   └── graphql/                   # Definição do schema GraphQL
│       └── schema.graphql         # Schema da API
├── scripts/                       # Utilitários de desenvolvimento e teste
│   ├── create-user.js            # Script de criação de usuário
│   ├── create-chat.js            # Script de criação de chat
│   ├── send.js                   # Script de envio de mensagem
│   ├── subscribe.js              # Teste de subscription em tempo real
│   └── list-messages.js          # Script de recuperação de mensagens
├── frontend/                     # Diretório da aplicação frontend
├── Makefile                      # Automação de build
└── requirements.txt              # Dependências Python para desenvolvimento local
```

## Schema do banco de dados

### Tabelas

**Tabela Users**
- Chave primária: `id` (String)
- Atributos: `name`, `email`, `createdAt`

**Tabela Chats**
- Chave primária: `id` (String)
- GSI: `userId-createdAt` para listagem de chats por usuário
- Atributos: `userId`, `title`, `createdAt`

**Tabela Messages**
- Chave composta: `chatId` (PK), `sk` (SK) - formato: `timestamp#messageId`
- Atributos: `id`, `userId`, `role`, `content`, `createdAt`

## Schema da API

### Operações GraphQL

**Queries**
- `me`: dados do usuário atual
- `listChatsByUser`: sessões de chat do usuário
- `listMessages`: histórico de mensagens do chat

**Mutations**
- `createUser`: cadastro de usuário
- `createChat`: cria nova sessão de chat
- `sendMessage`: envia mensagem do usuário e dispara resposta da IA
- `addAssistantMessage`: adiciona resposta gerada pela IA
- `deleteChat`: remove sessão de chat

**Subscriptions**
- `onMessageSent`: atualizações de mensagens em tempo real

## Deploy

### Pré-requisitos

- AWS CLI configurado com as permissões adequadas
- Terraform >= 1.5.0
- Docker instalado
- Python 3.12+
- Node.js (para os scripts de teste)

### Deploy da infraestrutura

1. **Inicializar o Terraform**
   ```bash
   make init
   ```

2. **Planejar a infraestrutura**
   ```bash
   make plan
   ```

3. **Aplicar (deploy dos recursos)**
   ```bash
   make apply
   ```

4. **Destruir a infraestrutura**
   ```bash
   make destroy
   ```

### Variáveis de configuração

Principais variáveis do Terraform:
- `region`: região AWS de deploy (padrão: us-east-1)
- `project_name`: prefixo de nomeação dos recursos (padrão: chatbot)
- `bedrock_model`: modelo de IA selecionado (padrão: amazon.nova-micro-v1:0)
- `callback_urls`: callbacks de autenticação do Cognito
- `logout_urls`: redirects de logout do Cognito

## Desenvolvimento

### Testes locais

O diretório `scripts/` contém utilitários Node.js para testar a API:

- **Gestão de usuários**: criar e autenticar usuários
- **Operações de chat**: criar chats e enviar mensagens
- **Teste em tempo real**: assinar atualizações de mensagens
- **Recuperação de mensagens**: consultar histórico de conversas

### Configuração do ambiente

1. Configure as variáveis de ambiente a partir dos outputs do Terraform
2. Instale as dependências: `npm install` no diretório scripts
3. Rode os scripts de teste com as variáveis de ambiente adequadas

### Testando o orquestrador da Lambda

```bash
python3 -m venv .venv
.venv/bin/pip install -r infra/lambdas/orchestrator/requirements.txt -r config/requirements-dev.txt
.venv/bin/pytest --cov=app --cov-report=term-missing   # roda contra tests/, mockando AppSync + Bedrock
.venv/bin/ruff check .
.venv/bin/mypy
```

### Checando a configuração do Terraform

```bash
terraform -chdir=infra/terraform fmt -check -recursive
terraform -chdir=infra/terraform init -backend=false   # sem precisar de credenciais AWS
terraform -chdir=infra/terraform validate
```

## CI/CD

CI e deploy rodam no Jenkins da plataforma (`Jenkinsfile` → `appPipeline` da Shared Library `platform`, repo devops-platform), disparados por webhooks. Sem GitHub Actions.

- **PRs e branches** — validação do contrato; `docker build --target test` (`ruff check`, `ruff format --check`, `mypy`, `pytest` com cobertura ≥90% em Python 3.11 e 3.12 para a Lambda, mais `terraform fmt -check`, `init -backend=false` e `validate` em `infra/terraform`, versões das ferramentas no `config/requirements-dev.txt`); `pip-audit` no `infra/lambdas/orchestrator/requirements.txt`; Trivy (CRITICAL/HIGH) na imagem de runtime.
- **main** — tudo acima e depois build e smoke test da imagem da Lambda, release com o python-semantic-release (versão, CHANGELOG, tag e release no GitHub) e rebuild do portfolio. Também é reconstruída toda segunda para pegar patches de segurança. Nada é enviado para a AWS: o deploy (`terraform apply`, que chama o `docker-upload.sh` para construir `docker/Dockerfile --target runtime` e enviar ao ECR) continua sendo uma ação manual, disparada por um humano, contra infraestrutura AWS real.
- **Dependências** — Renovate (job `platform/renovate` no Jenkins, `renovate.json` → preset do devops-platform): atualizações diárias, manutenção semanal do lockfile, issue "Dependency Dashboard" e auto-merge de patch/minor depois que o Jenkins aprova.

## Segurança

### Métodos de autenticação

- **API Key**: para desenvolvimento e testes
- **Cognito User Pools**: autenticação de usuário em produção
- **AWS IAM**: autenticação serviço-a-serviço

### Controle de acesso

- Roles IAM com acesso de privilégio mínimo
- Diretivas de autorização do AppSync
- VPC endpoints para segurança adicional (opcional)

## Monitoramento

### Integração com CloudWatch

- Logging de requisições/respostas da API
- Métricas da função Lambda
- Monitoramento de performance do DynamoDB
- Rastreamento de erros em tempo real

### Métricas-chave

- Latência e throughput da API
- Tempo de cold start da Lambda
- Capacidade de leitura/escrita do DynamoDB
- Custos de invocação do Bedrock

## Otimização de custos

### Benefícios do serverless

- Modelo de precificação pay-per-use
- Escala automática conforme a demanda
- Sem overhead de manutenção de infraestrutura
- Alocação de recursos otimizada

### Considerações de performance

- Billing on-demand do DynamoDB
- Otimização de memória da Lambda
- Estratégias de cache do AppSync
- Seleção do modelo do Bedrock conforme o caso de uso
