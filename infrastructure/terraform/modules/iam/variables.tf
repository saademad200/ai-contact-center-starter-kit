variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for Lambda permissions"
  type        = string
}
