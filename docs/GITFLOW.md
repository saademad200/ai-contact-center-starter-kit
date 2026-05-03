# Git Branching Strategy — Alfalah GPT

This project follows a simplified **GitFlow** model with three long-lived branches.

---

## Branch Hierarchy

```
feature/* ──┐
bugfix/*  ──┤──► develop ──► release/rc ──► main
hotfix/*  ──┘                                │
                                             └── (tags: v1.x.x)
```

| Branch | Purpose | Deploys To | Direct Push |
|--------|---------|-----------|-------------|
| `main` | Production-stable, tagged releases | **Production** ECS | ❌ PR + 1 review |
| `release/rc` | Release candidate, pre-prod testing | **Staging** ECS | ❌ PR only |
| `develop` | Integration of all features | None (CI only) | ✅ Allowed |
| `feature/*` | Individual features | None | ✅ Allowed |
| `hotfix/*` | Emergency production fix | PR to `main` + `develop` | ✅ Allowed |

---

## Flow

### Normal Feature Work
```
git checkout develop
git checkout -b feature/my-feature
# ... work ...
git push origin feature/my-feature
# Open PR → develop
```

### Releasing to Staging
```
# When develop is stable and ready for QA:
git checkout release/rc
git merge develop --no-ff
git push origin release/rc
# ✅ Triggers staging deploy automatically
```

### Releasing to Production
```
# After QA sign-off on staging:
# Open PR: release/rc → main  (requires 1 reviewer approval)
# On merge → ✅ Triggers production deploy automatically
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### Hotfix
```
git checkout main
git checkout -b hotfix/critical-bug
# ... fix ...
# PR to main (reviewer required)
# PR to develop (keep branches in sync)
```

---

## Branch Protection Rules (Configure in GitHub → Settings → Branches)

### `main`
- ✅ Require a pull request before merging
- ✅ Require 1 approving review
- ✅ Dismiss stale reviews on new commits
- ✅ Require status checks: `Lint & Test`
- ✅ Do not allow bypassing the above settings
- ❌ Allow direct pushes: **OFF**
- ❌ Allow force pushes: **OFF**

### `release/rc`
- ✅ Require a pull request before merging
- ✅ Require status checks: `Lint & Test`
- ❌ Allow direct pushes: **OFF**
- ❌ Allow force pushes: **OFF**

---

## CI/CD Trigger Summary

| Event | Branch | Action |
|-------|--------|--------|
| Push / PR | Any | `ci.yml` — lint, SAST, tests |
| Merge PR | `release/rc` | `deploy-api.yml` + `deploy-frontend.yml` → **Staging** |
| Merge PR | `main` | `deploy-api.yml` + `deploy-frontend.yml` → **Production** |
