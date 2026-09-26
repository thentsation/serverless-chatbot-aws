terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.4.0"
    }
  }
}

provider "aws" {
  region = var.region
}

module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
}

module "cognito" {
  source        = "./modules/cognito"
  project_name  = var.project_name
  region        = var.region
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls
}

module "ecr" {
  source        = "./modules/ecr"
  project_name  = var.project_name
  region        = var.region
  docker_script = "${path.root}/../lambdas/orchestrator/docker-upload.sh"

}

module "iam" {
  source             = "./modules/iam"
  project_name       = var.project_name
  users_table_arn    = module.dynamodb.users_table_arn
  chats_table_arn    = module.dynamodb.chats_table_arn
  messages_table_arn = module.dynamodb.messages_table_arn
  lambda_arn         = module.lambda.orchestrator_lambda_arn
  appsync_api_arn    = module.appsync.api_arn
}

module "lambda" {
  source             = "./modules/lambda"
  project_name       = var.project_name
  region             = var.region
  ecr_repository_url = module.ecr.orchestrator_repository_url
  lambda_role_arn    = module.iam.lambda_role_arn
  appsync_url        = module.appsync.api_url
  appsync_api_key    = module.appsync.api_key
  bedrock_model      = var.bedrock_model
  bedrock_region     = var.bedrock_region
  depends_on         = [module.ecr]
}

module "cloudwatch" {
  source       = "./modules/cloudwatch"
  project_name = var.project_name
  api_id       = module.appsync.api_id
}

module "appsync" {
  source                   = "./modules/appsync"
  project_name             = var.project_name
  region                   = var.region
  schema_path              = "${path.module}/../graphql/schema.graphql"
  cognito_user_pool_id     = module.cognito.user_pool_id
  users_table              = module.dynamodb.users_table_name
  chats_table              = module.dynamodb.chats_table_name
  messages_table           = module.dynamodb.messages_table_name
  lambda_arn               = module.lambda.orchestrator_lambda_arn
  appsync_role_arn         = module.iam.appsync_role_arn
  cloudwatch_logs_role_arn = module.cloudwatch.logs_role_arn
}
