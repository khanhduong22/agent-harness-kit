---
name: use-constants
description: Enforce, define, and reuse enums and constants instead of hardcoded magic strings for roles, workflow stages, and states in index-cms.
---

# Use Constants for Reusable Variables

In the `index-cms` project (both admin panel and backend services), we strictly avoid hardcoding magic strings for roles, statuses, and workflow stages.

## Instructions
1. **Prohibit Hardcoded Strings**:
   - Do NOT use plain strings for role codes (e.g. `"strapi-super-admin"`, `"strapi-editor"`, `"strapi-author"`).
   - Do NOT use plain strings for workflow stages (e.g. `"draft"`, `"readyToReview"`, `"needsRevision"`, `"approved"`, `"rejected"`, `"deleted"`).

2. **Reuse Existing Constants**:
   - Before adding any state or role check, inspect the following files to check if the constants/enums are already declared:
     - `index-admin-cms/src/admin/constants/article.ts` (defines `WORKFLOW_STAGES`, `PUBLICATION_STATUS`, and `ADMIN_ROLES`)
     - `index-admin-cms/src/constants/workflow-stage.ts`

3. **Declaring New Constants**:
   - If a reusable string/value has no matching enum/constant, define it in a central configuration or constant file. 
   - Add detailed JSDoc comments or documentation describing the lifecycle and logic of the enum values (especially virtual states like `modified` status in Strapi 5).
