variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "service_name_suffix" {
  type = string
}

variable "cluster_id" {
  type = string
}

variable "ecs_task_execution_role_arn" {
  type = string
}

variable "ecs_task_iam_role_arn" {
  type = string
}

variable "ecr_repository_url" {
  type = string
}

variable "target_group_arn" {
  type = string
}

variable "security_group_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "cpu" {
  type    = number
  default = 512
}

variable "memory" {
  type    = number
  default = 1024
}

variable "efs_file_system_id" {
  type    = string
  default = ""
}

variable "efs_access_point_id" {
  type    = string
  default = ""
}

variable "extra_env_vars" {
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}
