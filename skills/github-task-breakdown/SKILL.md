---
name: github-task-breakdown
description: "Create tasks and sub-issues, break down epic/feature specs into implementation sub-issues with standardized Story Points via the est-point skill, link via GitHub Native Sub-Issues GraphQL, and populate GitHub Projects V2 fields (Status, Point Est, Point Act, Estimate, Type, Sprint). Triggers on 'create task', 'tạo task', 'create work', 'tạo sub issue', or 'break task'."
---

# GitHub Task Breakdown & Projects V2 Synchronization (Linked with `est-point`)

## Purpose
Automate the end-to-end lifecycle of creating and breaking down complex feature specifications, suggestions, bug reports, or epic issues into discrete, implementable sub-issues (Frontend, Backend, Admin CMS, Data), **calculating standardized Story Points using the [`est-point`](../est-point/SKILL.md) skill**, linking them into GitHub's native Sub-issues tree hierarchy, and populating **GitHub Projects V2** custom fields (`Status`, `Point Est`, `Point Act`, `Estimate`, `Type`, `Sprint` iterations) with zero manual data entry.

---

## When to Use This Skill
Activate this skill whenever:
- The user asks to "create task", "tạo task", "create work", "thêm task", "break task", "tạo sub issue", "tạo task FE/BE đối ứng", "phân rã tính năng", or "tạo issue bug vào sprint".
- The user requests assigning sub-tasks to a developer with Story Point estimates (`est-point`) and distributing across sprints (e.g. "điền point estimate và trải đều qua các sprint 60+").
- Synchronizing newly created or existing issues into a GitHub Project V2 table (updating columns: `Status`, `Point Est`, `Point Act`, `Estimate`, `Type`, `Sprint`, `Assignees`).

---

## 0. Mandatory Story Point Estimation via `est-point`

Starting from **Sprint 60**, the estimation system uses **Story Points (`Point Est` / `Point Act`)** governed by the **[`est-point`](../est-point/SKILL.md)** skill (TechPulse 2026 & Story Point Estimation Reference v1.0).

Before creating or updating any task/sub-issue/bug:
1. **Read & Apply `est-point`**:
   - Consult `~/.gemini/config/skills/est-point/SKILL.md` (or run `node ~/.gemini/config/skills/est-point/scripts/estimate.js`).
   - Match the task against the TechPulse 2026 Benchmark (`1.0 Point = 1 Standard Working Day`, scale `[0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0]`).
   - Apply TechPulse modifiers (`Senior = 0.5x`, `Junior = 1.0x`; Repeat `1st = 1.0x`, `2nd = 0.7x`, `3rd+ = 0.4x`) via:
     ```bash
     node ~/.gemini/config/skills/est-point/scripts/estimate.js search "<keyword>"
     node ~/.gemini/config/skills/est-point/scripts/estimate.js calc <juniorBasePoint> <senior|junior> <1|2|3>
     ```
   - Enforce the **Epic-as-a-Feature** anti-fragmentation and **No Double Counting** rules: any Epic > `3.0 Points` (Senior) MUST be decomposed into sub-tasks (`0.2 - 2.0 Points`), and points are recorded on leaf sub-issues only.
2. **Populate `Point Est` (and `Point Act`) in GitHub Projects V2 (`PVT_kwDODcsuC84BDOQk`)**:
   - `Point Est` (`PVTF_lADODcsuC84BDOQkzhoOFI0`): Required on every task/bug in Sprint 60+.
   - `Point Act` (`PVTF_lADODcsuC84BDOQkzhoOFJM`): Populate when the task is completed (`Done`).
   - **Planned Cap vs. Actual Delivery**: The `0.9 - 1.0 Pt/day` standard cap applies solely to **morning standup planning** (pre-flight daily report). Unplanned production bugs, regressions, or hotfixes executed during the day are estimated at their true standalone weight (`Point Est` & `Point Act`), and total actual daily output can naturally exceed 1.0 Pt (`1.2 - 1.5+ Pt`).

---

## 1. Discovery Phase: Parent Issue & Domain Scoping

Before creating any issue:
1. **Query Parent Issue & Existing Sub-Issues**:
   ```bash
   gh api graphql -f query='
   query($owner: String!, $repo: String!, $number: Int!) {
     repository(owner: $owner, name: $repo) {
       issue(number: $number) {
         id
         number
         title
         body
         subIssues(first: 50) {
           nodes {
             id
             number
             title
           }
         }
       }
     }
   }' -F owner="<owner>" -F repo="<repo>" -F number=<parentNumber>
   ```

2. **Formulate High-Quality Implementation Sub-Tasks**:
   For each sub-task, craft:
   - **Clean Title**: `[<Epic|US|Task|Bug>] [<BE|FE|Infra>] [<Repo>] [<Domain>] <Concise Action Title>`
     - `<Epic|US|Task|Bug>`: Work item level (default `Task` for active sprint/epic scope; only use `Bug` for confirmed post-QA regressions).
     - `<BE|FE|Infra>`: Engineering layer (`BE`, `FE`, `Infra`, `Data`, `Fullstack`).
     - `<Repo>`: Short repository identifier (`index-web`, `index-api`, `index-cms`, `index-data`, etc.).
     - `<Domain>`: Feature or page module (`Notifications`, `Home`, `Alerts`, `Community`, `Footer`, etc.).
     - Examples:
       - `[Task] [FE] [index-web] [Notifications] Implement Desktop Notification Dropdown UX`
       - `[Task] [BE] [index-api] [Notifications] Complete REPOST & ADMIN_REPLY flows`
       - `[Task] [BE] [index-cms] [Articles] Add auto-publish RBAC guard for editors`
   - **Structured Body**:
     ```markdown
     ### 📋 Thông tin Task (<Domain>)
     - **Sprint**: Sprint <N>
     - **Point Est**: <P> Point (`<CASE-ID>`: <Case Name>)
     - **Assignee**: @<username>
     - **Related Spec / Design**: #<specIssueId>
     - **Parent Epic**: #<parentNumber>

     ---

     ### 🎯 Mục tiêu & Phạm vi
     <Tóm tắt mục tiêu và hành vi kỳ vọng>

     **Phạm vi chi tiết**:
     - <Bullet point 1>
     - <Bullet point 2>

     ---

     ### 💻 Checklist triển khai
     - [ ] Phân tích layout / data contract
     - [ ] Xây dựng / tích hợp component UI & API
     - [ ] Viết unit tests & verify hồi quy
     ```

---

## 2. GitHub Native Sub-Issues Linking

GitHub now supports native sub-issues (hierarchy trees) via GraphQL mutation `addSubIssue`.

1. **Create the Child Issue**:
   ```bash
   ISSUE_URL=$(gh issue create \
     --repo "<owner>/<repo>" \
     --title "[Task] [FE] [index-web] [Home] Global Search Bar" \
     --assignee "<username>" \
     --body "<structured_body>")
   ```

2. **Link as Native Sub-Issue**:
   ```bash
   gh api graphql -f query='
   mutation($parentIssueId: ID!, $subIssueUrl: String!) {
     addSubIssue(input: {
       issueId: $parentIssueId,
       subIssueUrl: $subIssueUrl
     }) {
       issue { number }
       subIssue { number title }
     }
   }' -F parentIssueId="<PARENT_GRAPHQL_NODE_ID>" -F subIssueUrl="$ISSUE_URL"
   ```

---

## 3. GitHub Projects V2 Scope & Auth Guard

GitHub Projects V2 uses OAuth scope `project` (or `read:project`). If GitHub CLI does not have this scope, GraphQL queries touching `projectV2` fail with `INSUFFICIENT_SCOPES`.

### Automated Scope Check & 1-Click Refresh Protocol
When `gh project list` or `projectsV2` returns `INSUFFICIENT_SCOPES`:
1. Trigger non-interactive OAuth refresh with hostname:
   ```bash
   echo "Y" | gh auth refresh -h github.com -s project
   ```
2. Parse the one-time device code (e.g. `XXXX-XXXX`).
3. Copy the code to clipboard and open the authorization page:
   ```bash
   # macOS: echo -n "XXXX-XXXX" | pbcopy && open "https://github.com/login/device"
   # Linux: echo -n "XXXX-XXXX" | xclip -selection clipboard; xdg-open "https://github.com/login/device" 2>/dev/null || true
   # Windows (WSL2): echo -n "XXXX-XXXX" | clip.exe; cmd.exe /c start "https://github.com/login/device"
   ```
4. Notify the user in 1 line:
   > "Mã cấp quyền `XXXX-XXXX` đã được copy vào clipboard và tab trình duyệt đã mở. Bạn chỉ cần bấm Continue / Authorize để cấp quyền `project` cho GitHub CLI."

---

## 4. Projects V2 Field Resolution & Dynamic Iteration Provisioning

Once authenticated with `project` scope:
1. **Find Project ID & Field Schemas**:
   ```bash
   gh project list --owner "<owner>"
   gh project field-list <projectNumber> --owner "<owner>"
   ```

2. **Inspect Options & Configuration**:
   ```graphql
   query($projectId: ID!) {
     node(id: $projectId) {
       ... on ProjectV2 {
         fields(first: 50) {
           nodes {
             ... on ProjectV2SingleSelectField { id name options { id name } }
             ... on ProjectV2IterationField {
               id name
               configuration {
                 iterations { id title startDate duration }
               }
             }
             ... on ProjectV2FieldCommon { id name dataType }
           }
         }
       }
     }
   }
   ```

3. **Dynamic Iteration Provisioning (Adding Missing Sprints)**:
   If the project iteration field only defines Sprints up to e.g. Sprint 58, and the user asks to allocate tasks across Sprints 56 to 59, dynamically provision the new iteration:
   ```graphql
   mutation {
     updateProjectV2Field(input: {
       fieldId: "<ITERATION_FIELD_ID>",
       iterationConfiguration: {
         startDate: "<NEXT_START_DATE>",
         duration: 7,
         iterations: [
           { id: "<id_56>", title: "Sprint 56", startDate: "...", duration: 7 },
           { id: "<id_57>", title: "Sprint 57", startDate: "...", duration: 7 },
           { id: "<id_58>", title: "Sprint 58", startDate: "...", duration: 7 },
           { title: "Sprint 59", startDate: "2026-10-26", duration: 7 }
         ]
       }
     }) {
       projectV2Field {
         ... on ProjectV2IterationField {
           configuration { iterations { id title } }
         }
       }
     }
   }
   ```
   *Note: Pass existing iteration IDs to preserve them, omit `id` for new iterations to generate them.*

4. **Resolve Native Organization IssueType (`Task`)**:
   Query organization `issueTypes`:
   ```graphql
   query($org: String!) {
     organization(login: $org) {
       issueTypes(first: 10) { nodes { id name } }
     }
   }
   ```
   Match name `"Task"` -> `issueTypeId: "IT_kw..."`.

---

## 5. Batch Synchronization Engine (Story Point Automation Pattern)

For the **Index** GitHub Project V2 (`PVT_kwDODcsuC84BDOQk`), the canonical field IDs are:
- **`Status`**: `PVTSSF_lADODcsuC84BDOQkzg1NEQU` (`Backlog`: `f75ad846`, `Ready`: `08afe404`, `In progress`: `47fc9ee4`, `In review`: `4cc61d42`, `Ready for QA`: `22fec96b`, `Done`: `98236657`)
- **`Point Est`**: `PVTF_lADODcsuC84BDOQkzhoOFI0` (`NUMBER` — Story Points calculated via `est-point`)
- **`Point Act`**: `PVTF_lADODcsuC84BDOQkzhoOFJM` (`NUMBER` — Actual Story Points when completed)
- **`Estimate`**: `PVTF_lADODcsuC84BDOQkzg1NEgA` (`NUMBER` — legacy/parallel numeric estimate field)
- **`Sprint`**: `PVTIF_lADODcsuC84BDOQkzg1NEgE` (`Sprint 60`: `eb7091f1`, `Sprint 61`: `0760d96a`, `Sprint 62`: `73fee5ea`, `Sprint 63`: `f01d7afe`, `Sprint 64`: `c5ff0599`, `Sprint 65`: `97a30e92`, `Sprint 66`: `eef2ec0a`, `Sprint 67`: `aaac6376`, `Sprint 68`: `d97432d5`, `Sprint 69`: `5788f6b8`)
- **`Type`**: `PVTSSF_lADODcsuC84BDOQkzgz79-I` (`Task`: `997d2238`, `Bug`: `492c2999`, `Feat`: `0b98368f`, `Epic`: `b0245420`)

When updating 5+ tasks, execute batch updates via a Python/Node script with combined GraphQL aliases to avoid rate limits (note: always pass string IDs with `-f` in `gh api graphql` so all-digit option IDs like `98236657` are not coerced to integers):

```python
import subprocess
import time

PROJECT_ID = "PVT_kwDODcsuC84BDOQk"
STATUS_FIELD_ID = "PVTSSF_lADODcsuC84BDOQkzg1NEQU"
STATUS_READY_ID = "08afe404"
POINT_EST_FIELD_ID = "PVTF_lADODcsuC84BDOQkzhoOFI0"
POINT_ACT_FIELD_ID = "PVTF_lADODcsuC84BDOQkzhoOFJM"
SPRINT_FIELD_ID = "PVTIF_lADODcsuC84BDOQkzg1NEgE"
SPRINT_IDS = {60: "eb7091f1", 61: "0760d96a", 62: "73fee5ea"}
TYPE_TASK_ID = "IT_kwDODcsuC84BDOQk..."

items = [...]  # [{num, itemId, issueId, sprint, pointEst, pointAct}]

for it in items:
    mutation = f"""
    mutation {{
      mStatus: updateProjectV2ItemFieldValue(input: {{
        projectId: "{PROJECT_ID}",
        itemId: "{it['itemId']}",
        fieldId: "{STATUS_FIELD_ID}",
        value: {{ singleSelectOptionId: "{STATUS_READY_ID}" }}
      }}) {{ projectV2Item {{ id }} }}

      mPointEst: updateProjectV2ItemFieldValue(input: {{
        projectId: "{PROJECT_ID}",
        itemId: "{it['itemId']}",
        fieldId: "{POINT_EST_FIELD_ID}",
        value: {{ number: {it['pointEst']} }}
      }}) {{ projectV2Item {{ id }} }}

      mSprint: updateProjectV2ItemFieldValue(input: {{
        projectId: "{PROJECT_ID}",
        itemId: "{it['itemId']}",
        fieldId: "{SPRINT_FIELD_ID}",
        value: {{ iterationId: "{SPRINT_IDS[it['sprint']]}" }}
      }}) {{ projectV2Item {{ id }} }}
    }}
    """
    subprocess.run(["env", "-u", "GITHUB_TOKEN", "gh", "api", "graphql", "-f", f"query={mutation}"], check=True)
    time.sleep(0.3)  # Throttle for rate limits
```

---

## 6. Verification & Handover Checklist
Before concluding task breakdown:
- [ ] Every sub-issue has a parent link and is visible in GitHub Native Sub-Issues tree.
- [ ] Every task has an Assignee set.
- [ ] Every task has Status set to requested state (e.g. `Ready` or `Done`).
- [ ] Every task has **Story Points (`Point Est`)** calculated via `est-point` and filled in the Project table (`Point Act` also filled if `Done`).
- [ ] Tasks are balanced across target Sprints (no single sprint overloaded).
- [ ] Type column displays `Task` or `Bug` icon and corresponding label is attached.
- [ ] Handover report shows a clean Markdown table with direct issue links, sprint allocations, Casebook IDs, and Story Points (`Point Est` / `Point Act`).
