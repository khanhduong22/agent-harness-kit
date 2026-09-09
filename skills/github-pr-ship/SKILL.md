---
name: github-pr-ship
description: Automatically push current git branch and create or update Pull Request on GitHub using gh CLI with standardized PR template description during /ship phase.
---

# Automated GitHub PR Creation on `/ship`

Whenever the user invokes `/ship` or requests shipping a feature/task, follow this automated workflow. An explicit `/ship` invocation authorizes pushing the current task branch after all gates pass; outside `/ship`, ask before `git push`.

## Mandatory Workflow Steps:

1. **Execute Pre-Ship Mandatory Checklist**:
   - Run unit tests: `bun test src/<module>`
   - Run Postman E2E tests: `bun run test:postman` (for API services)
   - Run Playwright E2E tests & record video: `npx playwright test` + `./scripts/upload-e2e-video.sh` (mandatory for `index-admin-cms`)
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
   - **Pre-Ship Mandatory Checklist Table**: Verification table showing passing results for Unit Tests, API/Browser E2E, Code Simplification, Build, and Google Drive Video URL (mandatory for UI/CMS).

5. **Output Direct PR Link**:
   - Display the GitHub Pull Request URL directly to the user.

6. **Slack Handover Notification**:
   - For UI/CMS tasks, invoke `./scripts/notify-slack.sh` with the PR link, Google Drive video recording link, and key flow steps.
