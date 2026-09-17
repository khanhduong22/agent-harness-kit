# Agent Hooks

## ADDED Requirements

### Requirement: Hook scripts SHALL read their inputs from any supported host payload

The four hook scripts SHALL extract the edited file path, the command line, and the workspace directory using a fallback chain that accepts the Claude Code / Codex shape and the Antigravity shape, so one script serves every host.

#### Scenario: Claude Code sends a file edit

- **GIVEN** `prisma-auto-flow.sh` receives `{"tool_input":{"file_path":"/repo/prisma/api/schema.prisma"}}` on stdin
- **WHEN** the script extracts the target file
- **THEN** it resolves `/repo/prisma/api/schema.prisma`
- **AND** it announces the safe-migration flow for that file

#### Scenario: Antigravity sends the same edit in its own shape

- **GIVEN** the same script receives `{"toolCall":{"args":{"TargetFile":"/repo/prisma/api/schema.prisma"}}}` on stdin
- **WHEN** the script extracts the target file
- **THEN** it resolves the identical path
- **AND** it behaves exactly as it does for the Claude Code payload

#### Scenario: No workspace field is present

- **GIVEN** a payload carrying neither `cwd` nor `workspacePaths`
- **WHEN** a script needs the workspace directory
- **THEN** it falls back to the process working directory
- **AND** it does not abort

### Requirement: A blocking hook SHALL fail open

`guard-new-packages.sh` runs on `PreToolUse` for `Bash` and can refuse a command. It SHALL allow the command whenever it cannot reach a confident decision.

#### Scenario: The payload cannot be parsed

- **GIVEN** `guard-new-packages.sh` receives malformed JSON on stdin
- **WHEN** extraction fails
- **THEN** the script exits 0
- **AND** the operator's command proceeds

#### Scenario: An install of an unrequested package is attempted

- **GIVEN** the payload carries a command that installs a package
- **WHEN** the script inspects it
- **THEN** the command is blocked
- **AND** the reason names the package

### Requirement: The Stop gate SHALL block only where a loop guard exists

A Stop hook that blocks re-enters on the next stop attempt. Antigravity supplies `executionNum` to break that cycle; Claude Code and Codex send no equivalent. `stop-gate.sh` SHALL therefore block only when a loop guard is present in the payload, and SHALL otherwise surface its reminder without holding the turn open.

#### Scenario: Claude Code ends a turn with unverified source edits

- **GIVEN** `stop-gate.sh` receives a Stop payload carrying no `executionNum`
- **AND** the transcript shows at least three source edits and no verification run
- **WHEN** the hook runs
- **THEN** it emits the reminder as `systemMessage`
- **AND** it emits no blocking decision, so the turn cannot loop

#### Scenario: Antigravity ends a turn with unverified source edits

- **GIVEN** the same condition with `terminationReason` `model_stop` and `executionNum` 1
- **WHEN** the hook runs
- **THEN** it blocks the stop and states how many source files were modified

#### Scenario: Verification already ran

- **GIVEN** the transcript records a verification command
- **WHEN** the hook runs on any host
- **THEN** the stop is allowed

### Requirement: The Stop gate SHALL evaluate its own condition correctly

The gate SHALL determine whether verification ran using a test whose result is a usable boolean, so the gate cannot silently fail open on its own logic.

#### Scenario: No verification command appears in the transcript

- **GIVEN** the transcript contains no verification command
- **WHEN** the gate evaluates that condition
- **THEN** the evaluation succeeds and reports "not verified"
- **AND** it does not abort with a shell error and fall through to allow

### Requirement: Installing hooks SHALL preserve operator configuration

`install.sh` SHALL merge the kit's hook block into the target's settings without discarding entries the operator added, and without duplicating its own entries across reinstalls.

#### Scenario: An operator has their own hook on another event

- **GIVEN** the target settings already contain an operator hook on `SessionStart`
- **WHEN** `install.sh` deploys the kit's hooks
- **THEN** the operator's `SessionStart` hook is still present
- **AND** the kit's hooks are present alongside it

#### Scenario: The installer runs twice

- **GIVEN** the kit's hooks are already deployed
- **WHEN** `install.sh` runs again with no change
- **THEN** each kit hook appears exactly once
- **AND** the installer reports the hooks as unchanged

### Requirement: Deployed hooks SHALL be observed firing before the legacy config is retired

The workspace `.agents/hooks.json` SHALL remain in place until each migrated hook has been seen taking effect in a live session.

#### Scenario: A hook is configured but never observed

- **GIVEN** the hook block is present in the target settings
- **AND** no operator has seen the hook take effect
- **WHEN** retirement of `.agents/hooks.json` is considered
- **THEN** it is not retired
- **AND** the change is reported as unverified
