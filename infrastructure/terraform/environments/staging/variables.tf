variable "project" {
  type    = string
  default = "alfalah-ai"
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "alert_emails" {
  type    = list(string)
  default = ["admin@alfalahamc.com"]
}

variable "s3_bucket_name" {
  type    = string
  default = "alfalah-ai-data-staging"
}
