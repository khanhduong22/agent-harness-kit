---
name: github-automation
description: Automatically manage GitHub repository settings, secrets, and workflows using the gh CLI instead of asking the user to use the Web UI.
---

# GitHub CLI Automation

Whenever you need to interact with GitHub settings—such as creating repository secrets, triggering workflow runs, or checking workflow status—you MUST use the `gh` (GitHub CLI) tool directly instead of asking the user to perform manual actions in the GitHub web interface.

The user's local environment is already authenticated with `gh`. You can execute commands securely via the terminal.

## Key Actions:

### 1. Setting a Repository Secret
If a deployment or workflow requires a new environment variable or secret, add it automatically using `gh secret set`:
```bash
gh secret set SECRET_NAME -b "secret_value" --repo username/repo-name
```
*Never tell the user "Go to Settings -> Secrets and variables -> Actions". Just do it for them.*

### 2. Checking Workflow Status
To see the status of recent CI/CD deployments:
```bash
gh run list --repo username/repo-name --limit 5
```

### 3. Triggering or Rerunning Workflows
If a workflow failed because of missing secrets or temporary issues, rerun it:
```bash
# Rerun failed jobs in the latest run
gh run rerun $(gh run list --repo username/repo-name -L 1 --json databaseId -q ".[0].databaseId") --repo username/repo-name --failed
```

### 4. General Rule
Proactivity is key. If a task can be fully automated using the `gh` CLI, do it without waiting for user permission. Only ask the user to use the GitHub UI if it involves a destructive action (like deleting a repo) or something the CLI cannot handle.
