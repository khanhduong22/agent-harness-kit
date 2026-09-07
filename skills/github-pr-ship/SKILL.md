---
name: github-pr-ship
description: Automatically push current git branch and create or update Pull Request on GitHub using gh CLI with standardized PR template description during /ship phase.
---

# Automated GitHub PR Creation on `/ship`

Whenever the user invokes `/ship` or requests shipping a feature/task, follow this automated workflow. An explicit `/ship` invocation authorizes pushing the current task branch after all gates pass; outside `/ship`, ask before `git push`.

## Mandatory Workflow Steps:

1. **Execute Pre-Ship Mandatory Checklist**:
   - Run unit tests: `bun test src/<module>`
   - Run Postman E2E tests: `bun run test:postman`
   - Run linter & code simplification check: `bun run build`

2. **Git Commit & Push**:
   - Ensure changes are squashed into a single clean conventional commit.
   - Push the active branch to remote origin: `git push -u origin <branch-name>`.

3. **Automated PR Creation / Update via GitHub CLI (`gh`)**:
   - Execute `env -u GITHUB_TOKEN gh pr create --title "<Title>" --body-file <scratch-path>` (or `env -u GITHUB_TOKEN gh pr edit <pr-number> --title "<Title>" --body-file <scratch-path>`).
   - Use `env -u GITHUB_TOKEN` to bypass invalid ambient environment tokens and use the authenticated keyring user.

4. **PR Description Template Standard**:
   The PR body must contain:
   - **Summary & Motivation**: High-level problem statement and solution.
   - **Key Changes Breakdown**: Detailed bullet points of endpoints, database migrations, security fixes, and refactorings.
   - **Pre-Ship Mandatory Checklist Table**: 4-step verification table showing passing results for Unit Tests, Postman E2E, Code Simplification, and Build.

5. **Output Direct PR Link**:
   - Display the GitHub Pull Request URL directly to the user.
