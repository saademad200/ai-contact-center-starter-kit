variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (e.g. staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security groups for the ALB"
  type        = list(string)
}
