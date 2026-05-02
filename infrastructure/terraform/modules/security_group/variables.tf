variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (e.g. staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the security groups will be created"
  type        = string
}
