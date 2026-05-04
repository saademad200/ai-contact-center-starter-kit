# GitHub OIDC Identity Provider
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

variable "github_repo" {
  description = "GitHub repository (org/repo) allowed to deploy"
  type        = string
  default     = "saademad200/AI-Contact-Center"
}

data "aws_iam_role" "github_actions" {
  name = "github-actions-deploy-role"
}

# ECS full access (deploy, describe services)
resource "aws_iam_role_policy_attachment" "github_actions_ecs" {
  role       = data.aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
}

# ECR push/pull (build and push images)
resource "aws_iam_role_policy_attachment" "github_actions_ecr" {
  role       = data.aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser"
}

# Terraform state backend (S3 + DynamoDB lock)
resource "aws_iam_role_policy_attachment" "github_actions_terraform" {
  role       = data.aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}
