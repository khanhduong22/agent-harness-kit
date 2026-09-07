# Global AI Agent Mandatory Rules & Preferences

================================================================================
CATEGORY A: MINDSET & THINKING PROTOCOLS (BEFORE CODING)
================================================================================

## 1. Architectural Proposal, Debate & Best-Practice Standard
- **Pros & Cons Table First**: Whenever proposing 2 or more architectural solutions or technical approaches, ALWAYS present a concise comparative Markdown Table (Columns: `Option`, `Pros`, `Cons`, `Performance & Complexity`, `Recommendation`) FIRST before providing detailed explanations.
- **Debate & Push-Back First**: If a request seems unreasonable, inefficient, or violates software engineering best practices, YOU MUST CONFIRM AND DEBATE with me first. Do NOT blindly execute bad requests. Push back, propose the best practice, and wait for consensus before proceeding.
- **Best-Practice First Architecture**: Always design and implement production-grade, highly scalable best-practice architecture (e.g. DB triggers/counter columns for relation counts over runtime `COUNT(*)`, proper indexing, modular boundaries, type safety). Never settle for superficial "just working" quick-and-dirty patches that degrade system performance or maintainability.
- **Visual Diagrams (Mermaid Standard)**: Include Mermaid workflow/sequence diagrams (`mermaid`) in non-trivial implementation plans, architecture proposals, and specifications.

## 2. The 7-Rung Ladder (Ponytail Mindset / Lazy Senior Dev Standard)
"The best code is the code you never wrote. Lazy means efficient, not careless."
Before writing or modifying any code, the agent MUST stop at the first rung that holds:
1. **Does this need to exist at all?** (YAGNI) -> Speculative need = skip it, say so in one line.
2. **Already in this codebase?** -> Reuse existing helpers, utilities, types, BaseRepositories, Shared DTOs. Look before you write; never re-implement what's a few files over.
3. **Stdlib does it?** -> Use built-in JS/TS/Node/Bun standard library APIs.
4. **Native platform feature covers it?** -> HTML/CSS native controls (`<input type="date">`), PostgreSQL constraints/triggers/indexes over app-level custom code.
5. **Already-installed dependency solves it?** -> Use packages already in `package.json`. Never install a new package for what a few lines can do.
6. **Can it be one line?** -> One line.
7. **Only then:** Write the absolute minimum code that works.
- **Lazy about the solution, never about reading**: Read the code, trace the real flow end-to-end, and grep all callers before climbing the ladder.
- **Bug fix = Root cause, not symptom**: Fix the bug once at the shared source/function where all callers route through, rather than patching symptoms across multiple callers.
- **Safety is never on the chopping block**: Trust-boundary validation, type safety, auth/security checks, data integrity, error recovery, and accessibility must always be 100% preserved.

================================================================================
CATEGORY B: SDLC WORKFLOW & GATE CONTROLS
================================================================================

## 3. Main SDLC Workflow (OpenSpec + Addy Osmani Pipeline)
Always follow the 6-Phase Software Development Lifecycle (SDLC) pipeline:
`OPENSPEC (/opsx) ──▶ PLAN (/plan) ──▶ BUILD (/build) ──▶ VERIFY (/test) ──▶ REVIEW (/review) ──▶ SHIP (/ship)`
- **`/opsx`** (`openspec`): Create Deep OpenSpec change proposals (`openspec/changes/<change-name>/`: `proposal.md`, `design.md`, `tasks.md`, `specs/<capability>/spec.md` delta diffs) using mandatory Gherkin syntax (`GIVEN` / `WHEN` / `THEN` / `AND`) referencing permanent capabilities (`openspec/specs/<capability>/spec.md`).
- **`/plan`** (`planning-and-task-breakdown`): Create bite-sized TDD implementation task breakdowns in `<repo>/openspec/changes/<change-name>/tasks.md`.
- **`/build`** or **`/build auto`** (`incremental-implementation`): Execute implementation task-by-task.
- **`/test`** (`test-driven-development`): Run TDD red-green-refactor loop and verify test suites.
- **`/review`** (`code-review-and-quality` / `code-simplification` / `performance-optimization` / `security-and-hardening`): Audit code smells, simplify complexity, optimize web performance, and execute security hardening.
- **`/ship`** (`shipping-and-launch`): Verify git status and quality gates, archive any active OpenSpec change with `openspec archive <change-name> -y` **before the final commit**, stage explicit files, create the single commit, push, and create/update the PR. Use `--skip-specs` only when the change intentionally has no spec deltas. Invoking `/ship` is explicit authorization to push the current task branch after all gates pass.

## 4. SDLC Phase Gate Control Rule
- ✋ **Mandatory Stop Between Phases**: When executing the SDLC pipeline, YOU MUST STOP and wait for explicit user approval after completing EACH phase before proceeding to the next (e.g. stop after `/opsx` to get spec approval, stop after `/plan` to get plan approval).
- ⚡ **Autonomous Execution Exception**: You are ONLY allowed to proceed across phases automatically if the user explicitly requests an autonomous run (e.g., using `/build auto`, "chạy hết đến phase cuối", or "tự động làm từ A đến Z").

## 5. Bilingual Intent Mapping (Tiếng Việt ➔ SDLC Commands)
- **Tạo feature mới / Ý tưởng / Giao diện / Thiết kế / Spec** ➔ Kích hoạt `/opsx` (`openspec`, `interview-me`, `idea-refine`)
- **Lập plan / Kế hoạch công việc / Chia task** ➔ Kích hoạt `/plan` (`planning-and-task-breakdown`)
- **Bắt đầu code / Sửa code / Bắt đầu làm** ➔ Kích hoạt `/build` (`incremental-implementation`)
- **Chạy test / Fix bug / Báo lỗi / Crash** ➔ Kích hoạt `/test` (`debugging-and-error-recovery`, `test-driven-development`)
- **Kiểm tra linter / Code smells / Clean code / Review** ➔ Kích hoạt `/review` (Tự động kích hoạt đồng thời cả 4 review skills)
- **Đóng gói / Commit / Push / Xong task** ➔ Kích hoạt `/ship` (`shipping-and-launch`, `git-workflow-and-versioning`)

================================================================================
CATEGORY C: QUALITY, SAFETY & SHIPPING GATES
================================================================================

## 6. Dangerous Operations Require Confirmation & Git Safety
- 🚫 **Database Resets & Destructive Operations**: Always ask for explicit user confirmation before running DB resets, dropping tables, or executing destructive migrations (`prisma migrate reset`, `drop database`).
- 🚫 **Git Safety**: Outside an explicit `/ship`, ask before running `git push`. Invoking `/ship` authorizes pushing the current task branch after all gates pass. Stage specific modified files explicitly (never run `git add .` or `git add -A`).
- 🚧 **Parallel Change Isolation (MANDATORY)**: Before starting or continuing an OpenSpec/code change, inspect whether the current worktree already owns a different active change. If it does, MUST load and follow the `parallel-worktree-isolation` skill before editing any file. Independent changes MUST use their own branch and a managed worktree under `~/.agent-worktrees/<repo>/<branch-slug>`; dependent changes MUST use a stacked branch or wait for their prerequisite. Never mix two independent changes into one worktree, commit, or PR. After `/ship` leaves a managed worktree clean, unlock it so the global retention sweeper can remove it after merge.
- 📝 **Conventional Commits & 1-Commit Rule**: Every PR MUST contain EXACTLY ONE single commit. If multiple commits exist before pushing, run `git reset --soft origin/develop` and create a single commit with Start-Case Conventional Commit message (e.g. `Feat: Add New Feature`).

## 7. Code Quality, Scope Integrity & Evidence Gate
- **Mandatory 100% Gherkin ➔ Integration Test (IT) Coverage Gate**: AI agents are **STRICTLY PROHIBITED** from declaring `/test` complete or inviting user review without verifying that **EVERY SINGLE Gherkin `Scenario:` (`GIVEN` / `WHEN` / `THEN` / `AND`) in active OpenSpec specs has an automated Postman Newman test request in `postman/collections/`**. The agent MUST output a Gherkin-to-IT Coverage Matrix (`Spec Scenario` ➔ `Newman Request` ➔ `Pass`) with runtime evidence before declaring done. NEVER wait for user reminders.
- **No Silent Error Swallowing**: Fix root causes; never mask errors with empty `catch` blocks or suppress types with `@ts-ignore`.
- **Evidence Before Assertions**: Never claim a task is fixed or complete without running runtime verification commands (`bun test`, `bun run test:postman`, `bun run lint`) and showing passing results.
- **Strict Scope Focus**: Modify only files relevant to the current task. Do not refactor or reformat unrelated code.
- **No Unrequested Packages**: Ask before installing new dependencies or npm packages.
- **Secrets Hygiene**: Never hardcode API keys, tokens, or credentials in code files; use `.env`.

## 8. Mandatory Quad-Skill Execution on `/review` Command
- **Quad-Skill Trigger**: Whenever the user types `/review`, `/code-review`, or requests a code review, YOU MUST AUTOMATICALLY execute and combine all 4 review skills sequentially without skipping any:
  1. `code-review-and-quality` (Multi-axis 5-dimension review)
  2. `code-simplification` (Refactoring & readability simplification)
  3. `performance-optimization` (Query & runtime performance check)
  4. `security-and-hardening` (Vulnerability, auth, input validation & OWASP audit)
- **Output Standard**: Produce a unified 4-quadrant quality, simplification, performance, and security audit report.

## 9. Pre-Ship Mandatory Checklist Execution
- **Pre-Ship Gate**: Before shipping or declaring any task complete, invoke the `pre-ship-checklist` skill and execute `bun run verify:all`. All 7 verification gates are hard blockers — any failure blocks shipping.
