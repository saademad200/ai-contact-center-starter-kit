output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "api_blue_target_group_arn" {
  value = aws_lb_target_group.api_blue.arn
}

output "api_blue_target_group_name" {
  value = aws_lb_target_group.api_blue.name
}

output "frontend_blue_target_group_arn" {
  value = aws_lb_target_group.frontend_blue.arn
}

output "frontend_blue_target_group_name" {
  value = aws_lb_target_group.frontend_blue.name
}


output "alb_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}
