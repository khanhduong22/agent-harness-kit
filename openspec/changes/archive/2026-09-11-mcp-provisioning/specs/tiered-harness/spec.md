## MODIFIED REQUIREMENTS

### Requirement: Project Pack Isolation and Idempotency
The harness MUST support injecting modular project packs strictly to project targets with rollback capabilities, including MCP server configuration and tool allowlists.

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

#### Scenario: MCP Configuration Stays Inside The Target Project
GIVEN two project directories that each received a project pack install
WHEN the installer writes MCP configuration for the first project
THEN the MCP configuration is written only under the first project path
AND the second project's MCP configuration is left byte-for-byte unchanged
AND no MCP server declared by a project pack is written to a global harness config
