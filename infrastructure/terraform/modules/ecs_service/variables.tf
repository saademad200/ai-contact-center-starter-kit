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

# ── Autoscaling ───────────────────────────────────────────────────────────────

variable "cluster_name" {
  description = "ECS cluster name (required when enable_autoscaling = true)"
  type        = string
  default     = ""
}

variable "enable_autoscaling" {
  description = "Enable Application Auto Scaling for this ECS service"
  type        = bool
  default     = false
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 4
}

variable "autoscaling_cpu_target" {
  description = "Target CPU utilisation % to trigger scaling"
  type        = number
  default     = 60
}

variable "autoscaling_memory_target" {
  description = "Target memory utilisation % to trigger scaling"
  type        = number
  default     = 70
}
