resource "aws_secretsmanager_secret" "api" {
  name                    = "${var.project}-${var.environment}/api"
  description             = "API secrets for ${var.project} ${var.environment}"
  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
    Project     = var.project
  }
}
