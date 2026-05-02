output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = module.load_balancer.alb_dns_name
}

output "ecr_repository_url" {
  value = module.ecr.ecr_repository_url
}

output "s3_bucket_name" {
  value = module.s3.bucket_id
}
