# Infrastructure Implementation Checklist

Based on the required Alfalah Investments architecture and the provided `sample` infrastructure format, the following modules and environments need to be implemented.

## Terraform Modules (Reusable Components)
- [x] **Networking (`vpc`):** VPC, Public/Private Subnets, NAT Gateways, Route Tables.
- [x] **Security Groups (`security_group`):** ALB SG (port 80), ECS SG (port 8000), Lambda SG.
- [x] **Load Balancer (`load_balancer`):** Application Load Balancer (HTTP only), Target Groups.
- [x] **ECS (`ecs`):** Fargate Cluster, Task Definitions, ECS Service for FastAPI Backend.
- [x] **ECR (`ecr`):** Container registry for the FastAPI backend image.
- [x] **DynamoDB (`dynamodb`):** Tables for `alfalah-prompt-registry`, `alfalah-model-registry`, `conversations`, `messages`, `response-ratings`.
- [x] **S3 (`s3`):** Bucket for raw docs and cleaned JSONL. Includes bucket policies and event notifications to trigger Lambda.
- [x] **Lambda (`lambda`):** Text cleaning and JSONL formatting function, packaged and deployed.
- [x] **IAM (`iam`):** ECS Task Execution Role, ECS Task Role, Lambda Execution Role (with S3 read/write permissions).
- [x] **Observability/Alerting (`sns`):** SNS Topics for ECS deployment failures or ticket escalations.

## Environments
- [x] **Staging (`environments/staging`):** Wires up all the modules above with staging variables (e.g., lower capacity, dev Langfuse/OpenAI keys).
- [x] **Production (`environments/prod`):** High-availability setup, stricter IAM policies, larger capacity, prod keys.

## CI/CD (GitHub Actions)
- [ ] **Terraform Workflow:** Automate `terraform plan` on PR and `terraform apply` on merge to `infrastructure` branch.
- [ ] **Staging Deployment:** Build Docker image and trigger ECS rolling update to staging.
- [ ] **Production Deployment:** Build Docker image and deploy to prod behind manual approval gate.

## Currently Completed
- [x] Initial folder structure for terraform `environments` and some `modules`.
- [x] Base `docker-compose.yml` for local testing.

## Remaining
- [x] Hooking up the S3 event notification to the Lambda module.
- [x] Writing the actual Python code for the Lambda function.
