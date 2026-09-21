## MODIFIED REQUIREMENTS

### Requirement: Project Pack Isolation and Idempotency
The harness MUST support injecting modular project packs strictly to project targets with rollback capabilities, including MCP server configuration and tool allowlists.

#### Scenario: Project-Level Injection for Index
GIVEN an Index workspace directory at a designated project path
WHEN running `./scripts/install.sh --index --project-path /path/to/project --targets claude,codex`
THEN the project context file is written to `/path/to/project/AGENTS.md`, shared by both targets
AND the claude target writes no `/path/to/project/.claude/CLAUDE.md` and no `/path/to/project/CLAUDE.md`
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

## ADDED REQUIREMENTS

### Requirement: Legacy Project CLAUDE.md Migration
The harness SHALL migrate a project's legacy `CLAUDE.md` into `AGENTS.md` without losing content, and SHALL make the migration fully reversible.

#### Scenario: Legacy File Is Folded And Removed
GIVEN a project whose `.claude/CLAUDE.md` contains a kit marker block and the operator text `# Project Existing Rule`
WHEN running `./scripts/install.sh --index --project-path /path/to/project --targets claude`
THEN `/path/to/project/AGENTS.md` contains the kit marker block exactly once
AND `/path/to/project/AGENTS.md` contains `# Project Existing Rule` exactly once
AND `/path/to/project/.claude/CLAUDE.md` no longer exists
AND a byte-identical copy of the removed file exists in the run's backup directory

#### Scenario: Duplicate Text Is Not Folded Twice
GIVEN a legacy `CLAUDE.md` whose non-kit paragraphs already appear in `AGENTS.md`
WHEN the installer migrates it
THEN each of those paragraphs appears exactly once in `AGENTS.md`
AND the legacy file is removed

#### Scenario: Both Legacy Locations Migrate Without Collision
GIVEN a project with both `.claude/CLAUDE.md` and `CLAUDE.md`
WHEN the installer migrates them
THEN both files are backed up under distinct names
AND both are removed
AND the text of both is present in `AGENTS.md`

#### Scenario: Rollback Restores The Legacy File
GIVEN a completed migration
WHEN running `./scripts/install.sh --rollback latest`
THEN each removed legacy file is restored byte-for-byte
AND `AGENTS.md` returns to its pre-install content, or is removed if the run created it

#### Scenario: Symlinks Are Never Migrated
GIVEN a project whose `CLAUDE.md` is a symbolic link
WHEN the installer runs for the claude target
THEN the symbolic link is left untouched
AND a warning names the skipped path

#### Scenario: Dry Run Changes Nothing
GIVEN a project with a legacy `CLAUDE.md`
WHEN running the installer with `--dry-run`
THEN the output reports that the file would be migrated
AND no file is created, modified or removed

#### Scenario: Reinstall After Migration Is A No-Op
GIVEN a project that has already been migrated
WHEN re-running the installer with identical parameters
THEN `AGENTS.md` is reported unchanged
AND no new backup files are generated

#### Scenario: Failure Never Loses Content
GIVEN a project with a legacy `CLAUDE.md` whose `AGENTS.md` cannot be written
WHEN the installer runs for the claude target
THEN the legacy `CLAUDE.md` is still present and unmodified

### Requirement: Global Claude Rules Location
The harness SHALL keep installing the global Claude rules to `CLAUDE.md` in the Claude config directory, because Claude Code documents no user-level `AGENTS.md`.

#### Scenario: Global Rule Path Is Unchanged
GIVEN a fresh home directory
WHEN running `./scripts/install.sh --targets claude --rules`
THEN the rules are written to `<home>/.claude/CLAUDE.md`
AND no `<home>/.claude/AGENTS.md` is created

### Requirement: Claude Adapter States AGENTS.md Loading Accurately
The rendered Claude adapter rules SHALL describe how Claude Code loads `AGENTS.md` as verified, and SHALL NOT claim that `AGENTS.md` is never read.

#### Scenario: Rendered Adapter Carries The Verified Precedence Rule
GIVEN the rendered Claude adapter rules
WHEN the text is inspected
THEN it does not state that `AGENTS.md` is not an automatic Claude Code instruction source
AND it states that `CLAUDE.md` takes precedence over `AGENTS.md` when both exist in or above the working directory
AND it states that files under `.agents/` are not read and must be imported
