variable "bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to trigger on upload"
  type        = string
}
