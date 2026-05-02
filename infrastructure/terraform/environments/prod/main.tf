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
  vpc_cidr             = "10.2.0.0/16"
  public_subnet_cidrs  = ["10.2.1.0/24", "10.2.2.0/24"]
  private_subnet_cidrs = ["10.2.10.0/24", "10.2.11.0/24"]
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

module "ecs" {
  source                      = "../../modules/ecs"
  project                     = var.project
  environment                 = var.environment
  region                      = var.region
  ecr_repository_url          = module.ecr.ecr_repository_url
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_iam_role_arn       = module.iam.ecs_task_iam_role_arn
  target_group_arn            = module.load_balancer.blue_target_group_arn
  security_group_ids          = [module.security_group.ecs_tasks_security_group_id]
  private_subnet_ids          = module.vpc.private_subnet_ids
  desired_count               = 2 # High Availability for Prod
  cpu                         = 512
  memory                      = 1024
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

module "code_deploy" {
  source                       = "../../modules/code_deploy"
  project                      = var.project
  environment                  = var.environment
  region                       = var.region
  codedeploy_service_role_arn  = module.iam.codedeploy_service_role_arn
  cluster_name                 = module.ecs.cluster_name
  service_name                 = module.ecs.service_name
  alb_listener_arn             = module.load_balancer.alb_listener_arn
  blue_target_group_name       = module.load_balancer.blue_target_group_name
  green_target_group_name      = module.load_balancer.green_target_group_name
}
