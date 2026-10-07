#!/bin/bash

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Uso: $0 <REPO_URL> <IMAGE_NAME> <REGION>"
  exit 1
fi

REPO_URL="$1"
IMAGE_NAME="$2"
REGION="$3"

cd "$(dirname "$0")"

# Diretório temporário para evitar erro de credenciais
DOCKER_CONFIG_DIR="/tmp/docker-config"
mkdir -p "$DOCKER_CONFIG_DIR"

echo "Construindo a imagem Docker..."
docker build -t "$IMAGE_NAME:latest" .

echo "Marcando a imagem com o repositório ECR..."
docker tag "$IMAGE_NAME:latest" "$REPO_URL:latest"

echo "Autenticando com o Amazon ECR na região $REGION..."
aws ecr get-login-password --region "$REGION" | docker --config "$DOCKER_CONFIG_DIR" login --username AWS --password-stdin "$REPO_URL"

echo "Enviando a imagem para o Amazon ECR..."
docker --config "$DOCKER_CONFIG_DIR" push "$REPO_URL:latest"

echo "Imagem '$IMAGE_NAME' enviada com sucesso para o repositório $REPO_URL"
    