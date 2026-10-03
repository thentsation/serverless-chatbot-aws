# CI (o Jenkins roda docker build --target test): ruff, mypy e pytest com cobertura
# mínima de 90% em Python 3.11 e 3.12 para a Lambda orchestrator, nas versões fixadas em
# config/requirements-dev.txt (atualizadas pelo Renovate), e terraform fmt/validate da
# infra. pip-audit e Trivy rodam no pipeline da plataforma, fora do cache de build, porque
# o resultado muda com as bases de vulnerabilidades.
FROM python:3.12-slim AS lint

WORKDIR /app

COPY infra/lambdas/orchestrator/requirements.txt ./infra/lambdas/orchestrator/
COPY config/requirements-dev.txt ./config/

RUN pip install --no-cache-dir -r ./infra/lambdas/orchestrator/requirements.txt \
    $(grep -E '^(ruff|mypy)==' ./config/requirements-dev.txt)

COPY . .

RUN ruff check . && ruff format --check . && mypy && touch /ok

FROM python:3.11-slim AS pytest-py311

WORKDIR /app

COPY infra/lambdas/orchestrator/requirements.txt ./infra/lambdas/orchestrator/
COPY config/requirements-dev.txt ./config/

RUN pip install --no-cache-dir -r ./infra/lambdas/orchestrator/requirements.txt \
    $(grep -E '^(pytest|pytest-cov)==' ./config/requirements-dev.txt)

COPY . .

RUN pytest --cov=app --cov-report=term-missing --cov-fail-under=90 --cov-config=pyproject.toml && touch /ok

FROM python:3.12-slim AS pytest-py312

WORKDIR /app

COPY infra/lambdas/orchestrator/requirements.txt ./infra/lambdas/orchestrator/
COPY config/requirements-dev.txt ./config/

RUN pip install --no-cache-dir -r ./infra/lambdas/orchestrator/requirements.txt \
    $(grep -E '^(pytest|pytest-cov)==' ./config/requirements-dev.txt)

COPY . .

RUN pytest --cov=app --cov-report=term-missing --cov-fail-under=90 --cov-config=pyproject.toml && touch /ok

# Sem backend nem credenciais da AWS: só baixa os providers do .terraform.lock.hcl.
FROM hashicorp/terraform:1.16.5 AS terraform

WORKDIR /app

COPY infra/terraform ./infra/terraform

RUN terraform -chdir=infra/terraform fmt -check -recursive \
    && terraform -chdir=infra/terraform init -backend=false -input=false \
    && terraform -chdir=infra/terraform validate \
    && touch /ok

FROM scratch AS test

COPY --from=lint /ok /lint.ok
COPY --from=pytest-py311 /ok /pytest-py311.ok
COPY --from=pytest-py312 /ok /pytest-py312.ok
COPY --from=terraform /ok /terraform.ok

# Imagem da Lambda orchestrator (enviada ao ECR por infra/lambdas/orchestrator/docker-upload.sh,
# chamado pelo terraform apply; nada é publicado pelo Jenkins).
FROM public.ecr.aws/lambda/python:3.14 AS runtime

# A imagem base trava o releasever na versão do build: --releasever=latest pega os
# patches de segurança publicados depois dela.
RUN dnf upgrade -y --releasever=latest && dnf clean all && rm -rf /var/cache/dnf

COPY infra/lambdas/orchestrator/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY infra/lambdas/orchestrator/app.py ./

ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

CMD ["app.handler"]

# Fora da AWS a imagem sobe o Runtime Interface Emulator na 8080: o healthcheck só
# confirma que ele está aceitando conexões (invocar o handler chamaria o AppSync e o Bedrock).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8080), timeout=4).close()"]
