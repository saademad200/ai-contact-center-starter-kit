terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket  = "alfalah-ai-terraform-state"
    key     = "prod/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.region
}

module "vpc" {
  source               = "../../modules/vpc"
  project              = var.project
  environment          = var.environment
  region               = var.region
  vpc_cidr             = "10.1.0.0/16"
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24"]
}

module "security_group" {
  source      = "../../modules/security_group"
  project     = var.project
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
}

module "iam" {
  source        = "../../modules/iam"
  project       = var.project
  environment   = var.environment
  region        = var.region
  s3_bucket_arn = module.s3.bucket_arn
}

module "dynamodb" {
  source      = "../../modules/dynamodb"
  project     = var.project
  environment = var.environment
  region      = var.region
}

module "ecr" {
  source      = "../../modules/ecr"
  project     = var.project
  environment = var.environment
  region      = var.region
}

module "sns" {
  source       = "../../modules/sns"
  project      = var.project
  environment  = var.environment
  region       = var.region
  alert_emails = var.alert_emails
}

module "load_balancer" {
  source             = "../../modules/load_balancer"
  project            = var.project
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  security_group_ids = [module.security_group.alb_security_group_id]
}

module "ecs_cluster" {
  source      = "../../modules/ecs_cluster"
  project     = var.project
  environment = var.environment
}

module "ecs_api" {
  source                      = "../../modules/ecs_service"
  project                     = var.project
  environment                 = var.environment
  region                      = var.region
  service_name_suffix         = "api"
  cluster_id                  = module.ecs_cluster.cluster_id
  ecr_repository_url          = module.ecr.api_repository_url
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_iam_role_arn       = module.iam.ecs_task_iam_role_arn
  target_group_arn            = module.load_balancer.api_blue_target_group_arn
  security_group_ids          = [module.security_group.ecs_tasks_security_group_id]
  private_subnet_ids          = module.vpc.private_subnet_ids
  desired_count               = 1
  cpu                         = 256
  memory                      = 512
  container_port              = 8000
}

module "ecs_frontend" {
  source                      = "../../modules/ecs_service"
  project                     = var.project
  environment                 = var.environment
  region                      = var.region
  service_name_suffix         = "front"
  cluster_id                  = module.ecs_cluster.cluster_id
  ecr_repository_url          = module.ecr.frontend_repository_url
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_iam_role_arn       = module.iam.ecs_task_iam_role_arn
  target_group_arn            = module.load_balancer.frontend_blue_target_group_arn
  security_group_ids          = [module.security_group.ecs_tasks_security_group_id]
  private_subnet_ids          = module.vpc.private_subnet_ids
  desired_count               = 1
  cpu                         = 256
  memory                      = 512
  container_port              = 80
}

module "lambda" {
  source               = "../../modules/lambda"
  project              = var.project
  environment          = var.environment
  region               = var.region
  lambda_exec_role_arn = module.iam.lambda_exec_role_arn
  subnet_ids           = module.vpc.private_subnet_ids
  security_group_ids   = [module.security_group.lambda_security_group_id]
}

module "s3" {
  source              = "../../modules/s3"
  region              = var.region
  bucket_name         = var.s3_bucket_name
  lambda_function_arn = module.lambda.function_arn
}

