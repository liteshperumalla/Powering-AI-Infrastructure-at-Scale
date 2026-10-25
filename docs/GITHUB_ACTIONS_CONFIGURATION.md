# GitHub Actions configuration

Secrets and variables used by the workflows in `.github/workflows/`. Set them under
**Settings → Secrets and variables → Actions**, or with the `gh` CLI as shown below.

Nothing here is required for the core pipeline: `ci-cd.yml` (tests, lint, type-check,
build, Docker, CodeQL, Trivy) and `security-scan.yml` run with only the automatic
`GITHUB_TOKEN`. Everything else switches on when you configure it.

## Variables (non-secret)

| Variable | Used by | Purpose |
|---|---|---|
| `STAGING_API_URL` | performance-test, monitoring-alerts | Base URL of the staging API, e.g. `https://api.staging.example.com` (no trailing slash). Enables scheduled load/stress tests against staging. |
| `PRODUCTION_API_URL` | performance-test, monitoring-alerts | Base URL of the production API. Used when a run selects `production`. |
| `MONITORING_ENABLED` | monitoring-alerts | Set to `true` to turn on the 15-minute health and performance monitoring jobs. Needs the `KUBE_CONFIG_*` secrets and the API URL variables. |

Variables are used instead of secrets for these on/off switches because GitHub doesn't
allow secrets in a job-level `if:`. A skipped job doesn't start a runner.

```bash
gh variable set STAGING_API_URL    --body "https://api.staging.example.com"
gh variable set PRODUCTION_API_URL --body "https://api.example.com"
gh variable set MONITORING_ENABLED --body "true"
```

## Secrets

### Used by active jobs

| Secret | Used by | What to put in it |
|---|---|---|
| `GITHUB_TOKEN` | ci-cd | Automatic; nothing to set. |
| `CLAUDE_CODE_OAUTH_TOKEN` | claude, claude-code-review | Token for the Claude Code GitHub workflows (create with `claude setup-token`). Probably already set if those workflows run. |
| `KUBE_CONFIG_PRODUCTION` | monitoring-alerts | Full kubeconfig file contents (raw YAML) for the production cluster. Use a read-only service account: the job only runs `kubectl get`. |
| `KUBE_CONFIG_STAGING` | monitoring-alerts | Same, for the staging cluster. |
| `SLACK_WEBHOOK_ALERTS` | monitoring-alerts | Slack incoming-webhook URL for health alerts. Optional; alerts are skipped if unset. |
| `SLACK_WEBHOOK` | ci-cd | Slack incoming-webhook URL for pipeline notifications. Optional; skipped if unset. |
| `SNYK_TOKEN` | security-scan | Snyk API token for the container image scan. Optional; skipped if unset. |
| `PERF_USER_EMAIL` | performance-test | Login for a dedicated, low-privilege test user in the target environment. Optional: without it the load test only hits `/health`. |
| `PERF_USER_PASSWORD` | performance-test | Password for that user. |

```bash
gh secret set KUBE_CONFIG_PRODUCTION < ~/.kube/prod-readonly.yaml
gh secret set KUBE_CONFIG_STAGING    < ~/.kube/staging-readonly.yaml
gh secret set SLACK_WEBHOOK_ALERTS   # prompts for the value
gh secret set SLACK_WEBHOOK
gh secret set SNYK_TOKEN
gh secret set PERF_USER_EMAIL
gh secret set PERF_USER_PASSWORD
```

### Referenced only by disabled steps

These belong to deploy and analysis steps in `ci-cd.yml` that are switched off with
`if: false`. Set them only when you enable those steps.

| Secret | Step |
|---|---|
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Deploy to Staging → Configure AWS credentials |
| `DOCKER_USERNAME`, `DOCKER_PASSWORD` | Deploy to Staging → registry login / image push |
| `SONAR_TOKEN` | Code Quality → SonarCloud scan |

## Environments

The deploy jobs in `ci-cd.yml` use GitHub environments named `staging` and `production`.
GitHub creates them on first use. Add protection rules (required reviewers, branch
restrictions) under **Settings → Environments** if deploys should need approval.

## Behaviour to be aware of

- Every push to `main` runs the `Deploy to Production` job, which creates a GitHub Release
  tagged `v<run number>`.
- The load test is read-only, and the stress test only hits `/health`. Neither creates data
  in the target environment.
