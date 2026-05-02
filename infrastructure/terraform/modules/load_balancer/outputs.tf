output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "blue_target_group_arn" {
  description = "ARN of the Blue Target Group"
  value       = aws_lb_target_group.blue.arn
}

output "blue_target_group_name" {
  description = "Name of the Blue Target Group"
  value       = aws_lb_target_group.blue.name
}

output "green_target_group_name" {
  description = "Name of the Green Target Group"
  value       = aws_lb_target_group.green.name
}

output "alb_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}
