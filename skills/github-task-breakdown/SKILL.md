---
name: github-task-breakdown
description: Automatically break down epic/feature specs into implementation sub-issues, link via GitHub Native Sub-Issues GraphQL, and populate GitHub Projects V2 fields (Status, Estimate, Type, Sprint).
---

# GitHub Task Breakdown & Projects V2 Synchronization

## Purpose
Automate the end-to-end lifecycle of breaking down complex feature specifications, suggestions, or epic issues into discrete, implementable sub-issues (Frontend, Backend, Admin CMS, Data), linking them into GitHub's native Sub-issues tree hierarchy, and populating **GitHub Projects V2** custom fields (Status, Estimate hours, Type, Sprint iterations) with zero manual data entry.

---

## When to Use This Skill
Activate this skill whenever:
- The user asks to "break task", "tạo sub issue", "tạo task FE/BE đối ứng", "phân rã tính năng".
- The user requests assigning sub-tasks to a developer with estimates and distributing across multiple sprints (e.g. "điền estimate và trải đều qua các sprint 56 - 59").
- Synchronizing newly created issues into a GitHub Project V2 table (updating columns: `Status`, `Estimate`, `Type`, `Sprint`, `Assignees`).

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
   - **Clean Title**: `[<Domain>] [<Feature/Page>] <Concise Action Title>` (e.g. `[FE] [Home] Global Search Bar` or `[CMS] Quản lý chiến dịch quảng cáo`).
   - **Structured Body**:
     ```markdown
     ### 📋 Thông tin Task (<Domain>)
     - **Sprint**: Sprint <N>
     - **Estimate**: <X>h
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
     --title "[FE] [Home] Global Search Bar" \
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
3. Copy the code to clipboard (`echo -n "XXXX-XXXX" | pbcopy`) and open the authorization page:
   ```bash
   open "https://github.com/login/device"
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

## 5. Batch Synchronization Engine (Python Automation Pattern)

When updating 5+ tasks, execute batch updates via a Python/Node script with combined GraphQL mutations to avoid rate limits:

```python
import subprocess
import time

PROJECT_ID = "PVT_kw..."
STATUS_FIELD_ID = "PVTSSF_..."
STATUS_READY_ID = "08afe404"
ESTIMATE_FIELD_ID = "PVTF_..."
SPRINT_FIELD_ID = "PVTIF_..."
SPRINT_IDS = {56: "ae074ea7", 57: "f551ff8d", 58: "8d5348e6", 59: "07a942fa"}
TYPE_TASK_ID = "IT_kw..."

items = [...]  # [{num, itemId, issueId, sprint, est}]

for it in items:
    mutation = f"""
    mutation {{
      mStatus: updateProjectV2ItemFieldValue(input: {{
        projectId: "{PROJECT_ID}",
        itemId: "{it['itemId']}",
        fieldId: "{STATUS_FIELD_ID}",
        value: {{ singleSelectOptionId: "{STATUS_READY_ID}" }}
      }}) {{ projectV2Item {{ id }} }}

      mEstimate: updateProjectV2ItemFieldValue(input: {{
        projectId: "{PROJECT_ID}",
        itemId: "{it['itemId']}",
        fieldId: "{ESTIMATE_FIELD_ID}",
        value: {{ number: {it['est']} }}
      }}) {{ projectV2Item {{ id }} }}

      mSprint: updateProjectV2ItemFieldValue(input: {{
        projectId: "{PROJECT_ID}",
        itemId: "{it['itemId']}",
        fieldId: "{SPRINT_FIELD_ID}",
        value: {{ iterationId: "{SPRINT_IDS[it['sprint']]}" }}
      }}) {{ projectV2Item {{ id }} }}

      mType: updateIssueIssueType(input: {{
        issueId: "{it['issueId']}",
        issueTypeId: "{TYPE_TASK_ID}"
      }}) {{ issue {{ id }} }}
    }}
    """
    subprocess.run(["gh", "api", "graphql", "-f", f"query={mutation}"], check=True)
    subprocess.run(["gh", "issue", "edit", str(it['num']), "--add-label", "task"], check=True)
    time.sleep(0.5)  # Throttle for rate limits
```

---

## 6. Verification & Handover Checklist
Before concluding task breakdown:
- [ ] Every sub-issue has a parent link and is visible in GitHub Native Sub-Issues tree.
- [ ] Every task has an Assignee set.
- [ ] Every task has Status set to requested state (e.g. `Ready`).
- [ ] Every task has numeric Estimate hours filled in Project table.
- [ ] Tasks are balanced across target Sprints (no single sprint overloaded).
- [ ] Type column displays `Task` icon and label `task` is attached.
- [ ] Handover report shows a clean Markdown table with direct issue links, sprint allocations, and estimates.
