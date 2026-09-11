/**
 * The gateway server: one endpoint in front of many upstreams.
 *
 * Three jobs, per Decision 1 in design.md — environment switching, composite
 * tools, and one registration line per harness. Everything else is proxied
 * through untouched.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type CallToolResult,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";

import { VERIFY_UI_TOOL_NAME, runVerifyUiAgainstFigma, verifyUiToolDefinition } from "./composite.js";
import {
  type GatewayConfig,
  exportedToolName,
  parseExportEntry,
  validateConfig,
} from "./config.js";
import { MountRegistry, type MountStatus } from "./upstream.js";

export const GATEWAY_STATUS_TOOL = "gateway_status";

/** Key under which `tools/list` reports mount health back to the client. */
export const MOUNTS_META_KEY = "kido-mcp-gateway/mounts";

const ENVIRONMENT_ARG = "environment";

export interface GatewayHandle {
  server: Server;
  registry: MountRegistry;
  /** Health of every mount, as of the last connection attempt. */
  status(): MountStatus[];
  close(): Promise<void>;
}

function environmentProperty(environments: string[]) {
  return {
    type: "string",
    enum: environments,
    description: `Connection environment. One of: ${environments.join(", ")}.`,
  };
}

/**
 * Re-describes an upstream tool under its exported name.
 *
 * The upstream's own schema is preserved; the only addition is the
 * `environment` parameter, which is what lets one tool serve local, dev, and
 * staging instead of three near-identical registrations.
 */
function reexport(tool: Tool, mount: string, environments: string[]): Tool {
  const schema = tool.inputSchema ?? { type: "object" as const };
  const properties: Record<string, object> = { ...(schema.properties ?? {}) };
  if (environments.length > 0) {
    properties[ENVIRONMENT_ARG] = environmentProperty(environments);
  }
  return {
    ...tool,
    name: exportedToolName(mount, tool.name),
    description: tool.description ?? `Proxied from upstream ${mount}.`,
    inputSchema: { ...schema, type: "object", properties },
  };
}

function statusText(statuses: MountStatus[]): string {
  return statuses
    .map((status) => {
      const where = status.environment ? `${status.name}@${status.environment}` : status.name;
      return status.ok
        ? `ok      ${where} (${status.toolCount ?? 0} tools)`
        : `FAILED  ${where}: ${status.error ?? "unknown error"}`;
    })
    .join("\n");
}

/**
 * Resolves the environment for one call.
 *
 * Returns an error message instead of throwing so the caller can refuse the
 * call *before* any upstream is touched — an unknown environment must make no
 * upstream call at all.
 */
export function resolveEnvironment(
  registry: MountRegistry,
  args: Record<string, unknown>,
): { environment: string | undefined; rest: Record<string, unknown> } | { error: string } {
  const { [ENVIRONMENT_ARG]: requested, ...rest } = args;
  const configured = registry.configuredEnvironments;

  if (requested === undefined) {
    return { environment: registry.defaultEnvironment, rest };
  }
  if (configured.length === 0) {
    return { error: `no environments are configured, so "${ENVIRONMENT_ARG}" cannot be set` };
  }
  if (typeof requested !== "string" || !configured.includes(requested)) {
    return {
      error:
        `unknown environment ${JSON.stringify(requested)}; ` +
        `configured environments are: ${configured.join(", ")}`,
    };
  }
  return { environment: requested, rest };
}

export function createGateway(config: GatewayConfig): GatewayHandle {
  validateConfig(config);
  const registry = new MountRegistry(config);
  const composite = config.composite?.verify_ui_against_figma;

  const server = new Server(
    { name: "kido-mcp-gateway", version: "0.1.0" },
    { capabilities: { tools: {} } },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    const statuses = await registry.mountAll();
    const environments = registry.configuredEnvironments;
    const tools: Tool[] = [];

    for (const entry of config.export) {
      const { mount, tool } = parseExportEntry(entry);
      const status = statuses.find((candidate) => candidate.name === mount);
      // A failed mount contributes no tools, but its failure is reported in
      // _meta below and through gateway_status — never silently dropped.
      if (!status?.ok) continue;
      const upstream = await registry.listTools(mount, registry.defaultEnvironment);
      const found = upstream.tools.find((candidate) => candidate.name === tool);
      if (!found) continue;
      tools.push(reexport(found, mount, environments));
    }

    if (composite) {
      tools.push(verifyUiToolDefinition(environments) as Tool);
    }

    tools.push({
      name: GATEWAY_STATUS_TOOL,
      description: "Report each mounted upstream as ok or failed, with its error.",
      inputSchema: { type: "object", properties: {} },
    });

    return { tools, _meta: { [MOUNTS_META_KEY]: statuses } };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request): Promise<CallToolResult> => {
    const name = request.params.name;
    const args = (request.params.arguments ?? {}) as Record<string, unknown>;

    if (name === GATEWAY_STATUS_TOOL) {
      const statuses = await registry.mountAll();
      return {
        isError: statuses.some((status) => !status.ok),
        content: [{ type: "text", text: statusText(statuses) }],
        _meta: { [MOUNTS_META_KEY]: statuses },
      };
    }

    const resolved = resolveEnvironment(registry, args);
    if ("error" in resolved) {
      return { isError: true, content: [{ type: "text", text: resolved.error }] };
    }

    if (composite && name === VERIFY_UI_TOOL_NAME) {
      return runVerifyUiAgainstFigma(registry, composite, resolved.rest, resolved.environment);
    }

    const entry = config.export.find((candidate) => {
      const { mount, tool } = parseExportEntry(candidate);
      return exportedToolName(mount, tool) === name || candidate === name;
    });
    if (!entry) {
      return {
        isError: true,
        content: [{ type: "text", text: `tool ${JSON.stringify(name)} is not exported by this gateway` }],
      };
    }

    const { mount, tool } = parseExportEntry(entry);
    try {
      return await registry.callTool(mount, resolved.environment, tool, resolved.rest);
    } catch (cause) {
      return {
        isError: true,
        content: [
          {
            type: "text",
            text: `upstream ${mount} failed to handle ${tool}: ${cause instanceof Error ? cause.message : String(cause)}`,
          },
        ],
      };
    }
  });

  return {
    server,
    registry,
    status: () => registry.statusReport(),
    close: async () => {
      await registry.close();
      await server.close();
    },
  };
}
