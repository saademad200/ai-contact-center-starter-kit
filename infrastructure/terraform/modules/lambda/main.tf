data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../../../lambda/s3_processor"
  output_path = "${path.module}/lambda_processor.zip"
}

resource "aws_lambda_function" "processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-s3-processor"
  role             = var.lambda_exec_role_arn
  handler          = "main.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 300
  memory_size      = 512

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-s3-processor"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.processor.function_name}"
  retention_in_days = 14
}
