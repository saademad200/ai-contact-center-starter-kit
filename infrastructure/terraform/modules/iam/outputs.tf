output "ecs_task_execution_role_arn" {
  value = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_iam_role_arn" {
  value = aws_iam_role.ecs_task_role.arn
}

output "lambda_exec_role_arn" {
  value = aws_iam_role.lambda_exec_role.arn
}

output "codedeploy_service_role_arn" {
  value = aws_iam_role.codedeploy_service_role.arn
}
