resource "aws_dynamodb_table" "prompt_registry" {
  name         = "${var.project}-${var.environment}-prompt-registry"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "version_id"

  attribute {
    name = "version_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project}-${var.environment}-prompt-registry"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "model_registry" {
  name         = "${var.project}-${var.environment}-model-registry"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project}-${var.environment}-model-registry"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "conversations" {
  name         = "${var.project}-${var.environment}-conversations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "conversation_id"

  attribute {
    name = "conversation_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project}-${var.environment}-conversations"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "messages" {
  name         = "${var.project}-${var.environment}-messages"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "conversation_id"
  range_key    = "timestamp_id"

  attribute {
    name = "conversation_id"
    type = "S"
  }

  attribute {
    name = "timestamp_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project}-${var.environment}-messages"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "ratings" {
  name         = "${var.project}-${var.environment}-response-ratings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "rating_id"

  attribute {
    name = "rating_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project}-${var.environment}-response-ratings"
    Environment = var.environment
  }
}
