# Terraform & OpenTofu Infrastructure-as-Code Guardrails (`antonbabenko/terraform-skill`)

Synthesized from [`antonbabenko/terraform-skill`](https://github.com/antonbabenko/terraform-skill) (`★ 2.4k+`). Load this reference when authoring, reviewing, or debugging Terraform / OpenTofu modules, remote state backends, or IaC CI/CD pipelines.

---

## 1. Diagnose-First IaC Failure Matrix

| Failure Mode | Root Cause | Production Fix |
|---|---|---|
| **Identity Churn (Accidental Destroy/Recreate)** | Using `count = length(var.subnets)` on lists where middle items can be removed or reordered | Always use `for_each = toset(var.subnets)` or `for_each = var.subnet_map` so resource addresses are keyed by stable name, never array index |
| **Refactor Address Drift** | Renaming a resource or splitting a module without state migration | Add declarative `moved { from = ... to = ... }` blocks (Terraform 1.1+) and verify `terraform plan` shows `0 to destroy` |
| **Secret Exposure in `terraform.tfstate`** | Marking a variable `sensitive = true` (which only masks CLI stdout while storing plaintext in state) | Use Terraform 1.11+ `write_only` (`*_wo`) arguments or inject secrets at runtime from AWS Secrets Manager / Vault / Cloudflare Secrets |
| **Destroy Cascade Surprise** | Running targeted destroy when `locals` reference the targeted resource across a `for_each` map | Never run `destroy` without `terraform plan -destroy` first; never pass `-auto-approve` to destroy |
| **CI Plan vs Apply Drift** | Running a fresh `terraform apply` in CI instead of applying the reviewed plan artifact | Save `terraform plan -out=tfplan.binary` in the PR/plan stage and run `terraform apply tfplan.binary` in the protected apply stage |

---

## 2. Module & State Architecture Standards

1. **3-Tier Hierarchy**:
   - **Resource Module** (single logical unit: VPC + subnets) $\to$ **Infrastructure Module** (regional stack) $\to$ **Composition** (`environments/prod/`, `environments/staging/`).
   - Never share a single state file between `prod` and `staging`.
2. **Modern Remote State Locking (`Terraform 1.10+`)**:
   - On AWS S3 backends with Terraform `1.10+` / OpenTofu, use native S3 lockfiles (`use_lockfile = true`, `encrypt = true`) instead of provisioning a separate DynamoDB lock table.
3. **Strict Variable & Output Contracts**:
   - Every `variable` block must follow the canonical order: `description` $\to$ `type` $\to$ `default` $\to$ `validation` $\to$ `nullable = false` $\to$ `sensitive`.
   - Prefer `optional(string, "default")` inside typed `object({...})` variables over untyped `map(any)`.
4. **Pre-Commit Verification Pipeline**:
   ```bash
   terraform fmt -check -recursive
   terraform validate
   tflint --recursive
   trivy config .
   ```
