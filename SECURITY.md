# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ Yes |
| Tagged releases | ✅ Yes |
| Older branches | ❌ No |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report them via one of these channels:

1. **GitHub Security Advisories (preferred):** [Open a private advisory](https://github.com/saademad200/AI-Contact-Center/security/advisories/new)
2. **Email:** Send details to the maintainer via the GitHub profile contact.

### What to Include

- Description of the vulnerability
- Steps to reproduce (minimal proof of concept)
- Potential impact
- Suggested fix (optional but appreciated)

---

## Response Timeline

| Stage | Target time |
|-------|------------|
| Acknowledgement | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix shipped | Within 30 days for critical, 90 days for others |
| Public disclosure | After fix is released |

---

## Security Design in This Project

This starter kit is built with security as a first-class concern:

| Control | Implementation |
|---------|---------------|
| **Secrets scanning** | `detect-secrets` pre-commit hook blocks any commit containing credentials |
| **SAST** | `bandit` + `semgrep` run on every commit via `.pre-commit-config.yaml` |
| **Dependency scanning** | Dependabot alerts (enable in your fork's settings) |
| **No static AWS keys** | GitHub Actions uses OIDC `role-to-assume` — no long-lived credentials |
| **Encrypted secrets** | All API keys stored in AWS Secrets Manager, never in ECS env vars |
| **Type safety** | `mypy` strict mode catches common logic errors |
| **CORS** | Configurable `cors_origins` setting — restrict in production |
| **JWT auth** | Admin panel protected with short-lived JWTs (configurable expiry) |
| **Audit trail** | All escalations and conversations logged to DynamoDB |

---

## Security Best Practices for Deployers

If you fork and deploy this kit:

1. **Set a strong `JWT_SECRET_KEY`** — `openssl rand -hex 32`
2. **Restrict `CORS_ORIGINS`** — do not leave `*` in production
3. **Enable Dependabot** on your fork
4. **Review IAM roles** in `infrastructure/terraform/modules/iam/` — scope them to your needs
5. **Rotate API keys** regularly and revoke unused ones in AWS Secrets Manager
6. **Enable AWS CloudTrail** for audit logs on all Secrets Manager access
7. **Review pre-commit output** before merging — do not bypass hooks with `--no-verify`
