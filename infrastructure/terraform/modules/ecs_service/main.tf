locals {
  use_efs = var.efs_file_system_id != ""

  mount_points = local.use_efs ? [
    {
      sourceVolume  = "chroma-data"
      containerPath = "/app/chroma_db"
      readOnly      = false
    }
  ] : []
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project}-${var.environment}-${var.service_name_suffix}"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_ecs_task_definition" "main" {
  family                   = "${var.project}-${var.environment}-${var.service_name_suffix}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu                   = var.cpu
  memory                = var.memory
  execution_role_arn    = var.ecs_task_execution_role_arn
  task_role_arn         = var.ecs_task_iam_role_arn

  dynamic "volume" {
    for_each = local.use_efs ? [1] : []
    content {
      name = "chroma-data"

      efs_volume_configuration {
        file_system_id     = var.efs_file_system_id
        transit_encryption = "ENABLED"

        authorization_config {
          access_point_id = var.efs_access_point_id
          iam             = "DISABLED"
        }
      }
    }
  }

  container_definitions = jsonencode([
    {
      name      = var.service_name_suffix
      image     = "${var.ecr_repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      environment = concat(
        [{ name = "ENVIRONMENT", value = var.environment }],
        var.extra_env_vars
      )

      mountPoints = local.mount_points
    }
  ])
}

resource "aws_ecs_service" "main" {
  name            = "${var.project}-${var.environment}-${var.service_name_suffix}-svc"
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.main.arn

  desired_count = var.desired_count
  launch_type   = "FARGATE"

  network_configuration {
    security_groups  = var.security_group_ids
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.service_name_suffix
    container_port   = var.container_port
  }

  tags = {
    Name        = "${var.project}-${var.environment}-${var.service_name_suffix}-svc"
    Environment = var.environment
  }
}