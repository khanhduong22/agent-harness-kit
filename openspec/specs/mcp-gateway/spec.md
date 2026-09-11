# mcp-gateway Specification

## Purpose
TBD - created by archiving change mcp-provisioning. Update Purpose after archive.
## Requirements
### Requirement: Gateway Re-Exports A Curated Subset Of Mounted Upstream Servers

The gateway SHALL mount upstream MCP servers as children and expose only the tools named in its `export` list, proxying calls to the owning upstream without copying upstream code.

#### Scenario: Only exported tools are visible

GIVEN a gateway mounting an upstream server that offers twenty-seven tools
AND an `export` list naming three of them
WHEN a client calls `tools/list` against the gateway
THEN exactly those three tools are returned
AND the remaining twenty-four are absent from the response

#### Scenario: A call reaches the owning upstream

GIVEN a gateway mounting two upstream servers that each export a tool
WHEN a client calls one of the exported tools
THEN the call is proxied to the upstream that owns that tool
AND the upstream's result is returned unmodified to the client

#### Scenario: An upstream failure is reported, not masked

GIVEN a gateway whose mounted upstream fails to start
WHEN a client calls `tools/list` against the gateway
THEN the gateway reports that upstream as failed
AND tools from healthy upstreams remain callable

### Requirement: Gateway Selects Connection Environment By Parameter

The gateway SHALL expose one tool per capability rather than one per environment, selecting the target environment from a parameter.

#### Scenario: One tool serves three environments

GIVEN a gateway configured with local, dev, and staging connection sets
WHEN a client calls an exported tool with the environment parameter set to `staging`
THEN the call uses the staging connection set
AND the gateway exposes a single tool for that capability rather than one tool per environment

#### Scenario: An unknown environment is refused

GIVEN a gateway configured with local, dev, and staging connection sets
WHEN a client calls an exported tool with an environment that is not configured
THEN the call fails with an error naming the configured environments
AND no upstream call is made

### Requirement: Gateway Reports Mount Health On Demand

The gateway SHALL provide a status command reporting each mounted upstream as ok or failed, so a broken mount is diagnosable without reading logs.

#### Scenario: Status distinguishes healthy from failed mounts

GIVEN a gateway with one reachable upstream and one unreachable upstream
WHEN the operator runs the gateway status command
THEN the reachable upstream is reported as ok
AND the unreachable upstream is reported as failed with its error
AND the command exits non-zero when any mount has failed

