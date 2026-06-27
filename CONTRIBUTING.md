# Contributing to AI Contact Center Starter Kit

Thank you for your interest in contributing! This project is an open-source starter kit — contributions that make it more useful, more adaptable, or better documented are all valued.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Issue Labels](#issue-labels)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

Be respectful. Constructive criticism is welcome; personal attacks are not. We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

---

## How to Contribute

### Reporting Bugs

1. Search [existing issues](https://github.com/saademad200/AI-Contact-Center/issues) first.
2. Open a new issue using the **Bug Report** template.
3. Include: what you expected, what happened, steps to reproduce, environment (OS, Python version, Docker version).

### Suggesting Features

1. Open an issue using the **Feature Request** template.
2. Describe the use case — what problem does this solve?
3. If it is a breaking change, note that explicitly.

### Good First Issues

Issues labeled [`good first issue`](https://github.com/saademad200/AI-Contact-Center/issues?q=label%3A%22good+first+issue%22) are scoped to be approachable without deep knowledge of the whole codebase. Great starting points.

---

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/AI-Contact-Center.git
cd AI-Contact-Center

# 2. Create a virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 5. Copy and configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY, LANGFUSE keys, etc.

# 6. Start local services
make dev

# 7. Run tests
make test-unit
make lint
```

---

## Pull Request Process

1. **Branch naming:** `feature/<short-description>`, `fix/<short-description>`, `docs/<short-description>`
2. **Keep PRs focused** — one logical change per PR.
3. **Write tests** for new code. Aim for unit tests on tools and services.
4. **Update documentation** if your change affects the README, ADRs, or any `docs/` file.
5. **Pass all CI checks** — lint, type check, unit tests must be green.
6. **Reference the issue** your PR fixes: `Closes #<issue-number>`.

PRs are reviewed within 48–72 hours on a best-effort basis.

---

## Issue Labels

| Label | Meaning |
|-------|---------|
| `good first issue` | Small, well-scoped, beginner-friendly |
| `enhancement` | New feature or improvement |
| `bug` | Something is broken |
| `documentation` | Docs-only change |
| `security` | Security-related issue or fix |
| `infrastructure` | Terraform, Docker, CI/CD changes |
| `help wanted` | Maintainer needs community help |

---

## Coding Standards

This project uses:
- **ruff** — linting (configured in `pyproject.toml`)
- **black** — code formatting
- **mypy** — static type checking
- **bandit** — security linting (SAST)
- **semgrep** — semantic code analysis
- **detect-secrets** — credential scanning

All of these run automatically as pre-commit hooks. Run manually:

```bash
make lint          # ruff + mypy
pre-commit run --all-files  # full suite
```

---

## Testing

```bash
make test-unit        # unit tests only (fast, no AWS)
make test-integration # integration tests (requires local DynamoDB)
```

New tool functions in `backend/app/agent/tools/` should have corresponding unit tests in `backend/tests/unit/`.

---

## Documentation

- **Architecture decisions** go in `docs/ARCHITECTURE_DECISIONS.md` as new ADRs.
- **Infrastructure changes** should update `docs/INFRASTRUCTURE_CHECKLIST.md`.
- **New tools** should be documented in the README tool table.

---

Thank you for contributing!
