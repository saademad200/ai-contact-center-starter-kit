locals {
  prefix = "${var.project}-${var.environment}"
  tags   = { Environment = var.environment }
}

resource "aws_dynamodb_table" "users" {
  name         = "${local.prefix}-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-users" })
}

resource "aws_dynamodb_table" "conversations" {
  name         = "${local.prefix}-conversations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-conversations" })
}

resource "aws_dynamodb_table" "messages" {
  name         = "${local.prefix}-messages"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-messages" })
}

resource "aws_dynamodb_table" "tickets" {
  name         = "${local.prefix}-tickets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-tickets" })
}

resource "aws_dynamodb_table" "documents" {
  name         = "${local.prefix}-documents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-documents" })
}

resource "aws_dynamodb_table" "response_ratings" {
  name         = "${local.prefix}-response-ratings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-response-ratings" })
}

resource "aws_dynamodb_table" "prompt_registry" {
  name         = "${local.prefix}-prompt-registry"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-prompt-registry" })
}

resource "aws_dynamodb_table" "model_registry" {
  name         = "${local.prefix}-model-registry"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = merge(local.tags, { Name = "${local.prefix}-model-registry" })
}
