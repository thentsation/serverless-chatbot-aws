resource "aws_cognito_user_pool" "pool" {
  name                     = "${var.project_name}-user-pool"
  auto_verified_attributes = ["email"]
  username_attributes      = ["email"]

  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name            = "${var.project_name}-client"
  user_pool_id    = aws_cognito_user_pool.pool.id
  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]
  supported_identity_providers  = ["COGNITO"]
  prevent_user_existence_errors = "ENABLED"

  # Configurações para fluxo web/navegador
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  # URLs de callback - ajuste conforme necessário
  callback_urls = var.callback_urls

  logout_urls = var.logout_urls

  # Configurações de token
  access_token_validity  = 60 # 1 hora
  id_token_validity      = 60 # 1 hora
  refresh_token_validity = 30 # 30 dias

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

# Domínio hospedado para URLs de login
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-${random_string.domain_suffix.result}"
  user_pool_id = aws_cognito_user_pool.pool.id
}

resource "random_string" "domain_suffix" {
  length  = 8
  special = false
  upper   = false
}