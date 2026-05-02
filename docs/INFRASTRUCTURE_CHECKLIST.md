# Infrastructure Implementation Checklist

Based on the required Alfalah Investments architecture and the provided `sample` infrastructure format, the following modules and environments need to be implemented.

## Terraform Modules (Reusable Components)
- [ ] **Networking (`vpc`):** VPC, Public/Private Subnets, NAT Gateways, Route Tables.
- [ ] **Security Groups (`security_group`):** ALB SG (port 80), ECS SG (port 8000), Lambda SG.
- [ ] **Load Balancer (`load_balancer`):** Application Load Balancer (HTTP only), Target Groups.
- [ ] **ECS (`ecs`):** Fargate Cluster, Task Definitions, ECS Service for FastAPI Backend.
- [ ] **ECR (`ecr`):** Container registry for the FastAPI backend image.
- [ ] **DynamoDB (`dynamodb`):** Tables for `alfalah-prompt-registry`, `alfalah-model-registry`, `conversations`, `messages`, `response-ratings`.
- [ ] **S3 (`s3`):** Bucket for raw docs and cleaned JSONL. Includes bucket policies and event notifications to trigger Lambda.
- [ ] **Lambda (`lambda`):** Text cleaning and JSONL formatting function, packaged and deployed.
- [ ] **IAM (`iam`):** ECS Task Execution Role, ECS Task Role, Lambda Execution Role (with S3 read/write permissions).
- [ ] **Observability/Alerting (`sns`):** SNS Topics for ECS deployment failures or ticket escalations.

## Environments
- [ ] **Staging (`environments/staging`):** Wires up all the modules above with staging variables (e.g., lower capacity, dev Langfuse/OpenAI keys).
- [ ] **Production (`environments/prod`):** High-availability setup, stricter IAM policies, larger capacity, prod keys.

## CI/CD (GitHub Actions)
- [ ] **Terraform Workflow:** Automate `terraform plan` on PR and `terraform apply` on merge to `infrastructure` branch.
- [ ] **Staging Deployment:** Build Docker image and trigger ECS rolling update to staging.
- [ ] **Production Deployment:** Build Docker image and deploy to prod behind manual approval gate.

## Currently Completed
- [x] Initial folder structure for terraform `environments` and some `modules`.
- [x] Base `docker-compose.yml` for local testing.

## Remaining
- [ ] Populating the `main.tf`, `variables.tf`, and `outputs.tf` for every single module based on the `sample` blueprint.
- [ ] Hooking up the S3 event notification to the Lambda module.
- [ ] Writing the actual Python code for the Lambda function.
