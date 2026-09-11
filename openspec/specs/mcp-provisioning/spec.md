# mcp-provisioning Specification

## Purpose
TBD - created by archiving change mcp-provisioning. Update Purpose after archive.
## Requirements
### Requirement: Profile-Declared MCP Servers Rendered To Native Harness Config

The system SHALL render MCP server declarations from a profile into each target harness's native MCP configuration file, scoped to the project given by `--project-path`.

#### Scenario: Installing the index pack writes a project-scoped MCP config

- **GIVEN** `profiles/index/api.md` declares an `[mcp.postgres]` server
- **WHEN** the operator runs `install.sh --index --project-path /path/to/index-api --targets claude`
- **THEN** `/path/to/index-api/.mcp.json` SHALL contain a `postgres` entry under `mcpServers`
- **AND** the file SHALL be written at the project root, not under `~/.claude/`

#### Scenario: A dry run writes nothing

- **GIVEN** a profile declaring at least one MCP server
- **WHEN** the operator runs the installer with `--dry-run`
- **THEN** the planned MCP config path SHALL be reported
- **AND** no file SHALL be created or modified on disk

#### Scenario: MCP writes are rolled back from the receipt

- **GIVEN** an install run that wrote a project `.mcp.json` and recorded it in `receipt.json`
- **WHEN** the operator runs `install.sh --rollback latest`
- **THEN** the `.mcp.json` SHALL be restored to its pre-install content
- **AND** a file that did not exist before the run SHALL be removed

#### Scenario: Secrets are rejected at verification time

- **GIVEN** a profile whose `[mcp.*]` block contains a literal credential rather than a `${VAR}` reference
- **WHEN** the operator runs `scripts/verify.sh`
- **THEN** verification SHALL fail
- **AND** the failure message SHALL name the offending profile and key
- **AND** the process SHALL exit with a non-zero status

#### Scenario: An unsupported target is explicit rather than silent

- **GIVEN** a target harness whose MCP config shape has not been verified
- **WHEN** the installer renders MCP config for that target
- **THEN** the installer SHALL report that the target is unsupported
- **AND** it SHALL NOT write a guessed configuration file

### Requirement: Profile-Declared Tool Allowlist Keeps Unlisted Tools Out Of Context

The system SHALL render a profile's `mcp_tools` allowlist into the target harness's permission configuration, merging with existing entries rather than replacing them.

#### Scenario: Only allowlisted tools are permitted

- **GIVEN** a profile whose `mcp_tools` lists `mcp__framefit__get_layout_spec` and nothing else from that server
- **WHEN** the operator installs the pack for that project
- **THEN** the rendered permission configuration SHALL contain `mcp__framefit__get_layout_spec`
- **AND** it SHALL NOT contain any other `mcp__framefit__` tool

#### Scenario: Existing user permissions survive a reinstall

- **GIVEN** a permission configuration containing an unrelated entry added by the operator
- **WHEN** the operator reinstalls the pack
- **THEN** the unrelated entry SHALL still be present
- **AND** the allowlisted MCP entries SHALL also be present

#### Scenario: Reinstalling produces no duplicate entries

- **GIVEN** a project already installed with an `mcp_tools` allowlist
- **WHEN** the operator runs the same install command a second time
- **THEN** each allowlist entry SHALL appear exactly once
- **AND** the run SHALL report the permission configuration as unchanged

