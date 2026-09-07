# Capability: Tiered Harness & Project Packs

## ADDED Requirements

### Requirement: Tiered Harness Routing and Autonomy Boundaries
The harness MUST support risk-based tiered workflows and explicit autonomy boundaries.

#### Scenario: Fresh Core Install
GIVEN a clean user environment without pre-existing configurations
WHEN running `./scripts/install.sh --targets claude,codex,gemini --rules`
THEN core skills and global rules are installed
AND project pack configurations (such as Index) are NOT present in global rules or skills
AND a backup receipt is created under `~/.agent-harness-backups/`

#### Scenario: Lightweight Bugfix Workflow Routing
GIVEN an AI agent configured with Core rules
WHEN a task is categorized as a minor bugfix or regression
THEN the agent does NOT mandate the creation of a full OpenSpec proposal and tasks document
AND the agent requires reproducing the failure, fixing the root cause, and running native test commands (`bun test`, `jest`)
AND the agent produces execution evidence before claiming task completion

#### Scenario: High-Risk Action Confirmation Gate
GIVEN an active implementation task
WHEN the agent encounters an operation involving database reset, dropping tables, destructive migrations, or pushing to remote git
THEN the agent MUST pause execution and ask for explicit user authorization
AND the agent must NOT perform the destructive operation automatically

### Requirement: Project Pack Isolation and Idempotency
The harness MUST support injecting modular project packs strictly to project targets with rollback capabilities.

#### Scenario: Project-Level Injection for Index
GIVEN an Index workspace directory at a designated project path
WHEN running `./scripts/install.sh --index --project-path /path/to/project --targets claude,codex`
THEN project-specific context files are written to `/path/to/project/.claude/CLAUDE.md` and `/path/to/project/AGENTS.md`
AND no global rules outside `/path/to/project` receive Index-specific rules
AND any unknown business requirements in the pack are explicitly tagged with `[TBD]`

#### Scenario: Idempotent Reinstallation
GIVEN an existing installation of Core or Project Pack
WHEN re-running the installer with identical parameters
THEN existing valid symlinks and marked rule blocks are recognized as unchanged
AND no duplicate entries, nested blocks, or redundant backup files are generated

#### Scenario: Rollback Restores Original State
GIVEN a completed installation that created new symlinks and modified project rules
WHEN running `./scripts/install.sh --rollback latest`
THEN all newly created symlinks are safely removed
AND modified files are restored to their pre-installation backup states
AND the workspace returns to its exact prior configuration
