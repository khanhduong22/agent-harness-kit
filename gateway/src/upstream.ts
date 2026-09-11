/**
 * Mounting and health of upstream MCP servers.
 *
 * One `MountRegistry` owns every connection the gateway holds. A connection is
 * keyed by `(mount name, environment)` because the environment parameter has to
 * change the connection, not just an argument — a `postgres` upstream pointed at
 * `staging` is a different process with a different `DATABASE_URL`.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import type { CallToolResult, ListToolsResult } from "@modelcontextprotocol/sdk/types.js";

import {
  type GatewayConfig,
  type UpstreamSpec,
  defaultEnvironment,
  environmentNames,
  isHttpUpstream,
} from "./config.js";

export interface MountStatus {
  name: string;
  environment: string | undefined;
  ok: boolean;
  /** Present only when `ok` is false. A failure is reported, never masked. */
  error?: string;
  toolCount?: number;
}

const GATEWAY_CLIENT_INFO = { name: "kido-mcp-gateway", version: "0.1.0" } as const;

/**
 * Resolves `${VAR}` references against the process environment.
 *
 * Secrets live in the environment, never in config, so a config value is either
 * a literal non-secret or a `${VAR}` reference that is resolved here.
 */
export function resolveEnvReferences(
  values: Record<string, string>,
  source: NodeJS.ProcessEnv = process.env,
): Record<string, string> {
  const resolved: Record<string, string> = {};
  for (const [key, value] of Object.entries(values)) {
    resolved[key] = value.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g, (_match, name: string) => {
      const found = source[name];
      if (found === undefined) {
        throw new Error(`environment variable ${name} referenced by ${key} is not set`);
      }
      return found;
    });
  }
  return resolved;
}

function connectionKey(name: string, environment: string | undefined): string {
  return environment === undefined ? name : `${name}@${environment}`;
}

export class MountRegistry {
  private readonly clients = new Map<string, Client>();
  private readonly transports = new Map<string, Transport>();
  private readonly statuses = new Map<string, MountStatus>();

  constructor(private readonly config: GatewayConfig) {}

  /** The environment a call falls back to when it names none. */
  get defaultEnvironment(): string | undefined {
    return defaultEnvironment(this.config);
  }

  get configuredEnvironments(): string[] {
    return environmentNames(this.config);
  }

  /**
   * Connects every mount under the default environment.
   *
   * A mount that throws is recorded as failed and the loop continues, so one
   * broken upstream never takes the healthy ones down with it.
   */
  async mountAll(): Promise<MountStatus[]> {
    const environment = this.defaultEnvironment;
    const results: MountStatus[] = [];
    for (const name of Object.keys(this.config.mount)) {
      results.push(await this.connect(name, environment));
    }
    return results;
  }

  /** Status of every connection attempt made so far, in mount order. */
  statusReport(): MountStatus[] {
    return Object.keys(this.config.mount).flatMap((name) =>
      [...this.statuses.values()].filter((status) => status.name === name),
    );
  }

  get failedCount(): number {
    return this.statusReport().filter((status) => !status.ok).length;
  }

  /**
   * Returns a connected client, connecting on first use.
   *
   * Throws when the upstream cannot be reached; the caller decides whether that
   * is a per-call error or a listed mount failure.
   */
  async client(name: string, environment: string | undefined): Promise<Client> {
    const key = connectionKey(name, environment);
    const existing = this.clients.get(key);
    if (existing) return existing;

    const status = await this.connect(name, environment);
    const client = this.clients.get(key);
    if (!client) {
      throw new Error(`upstream ${name} is unavailable: ${status.error ?? "unknown error"}`);
    }
    return client;
  }

  private async connect(name: string, environment: string | undefined): Promise<MountStatus> {
    const key = connectionKey(name, environment);
    const recorded = this.statuses.get(key);
    if (recorded && this.clients.has(key)) return recorded;

    const spec = this.config.mount[name];
    if (!spec) {
      const status: MountStatus = { name, environment, ok: false, error: `no mount named ${name}` };
      this.statuses.set(key, status);
      return status;
    }

    try {
      const transport = this.createTransport(spec, environment);
      const client = new Client(GATEWAY_CLIENT_INFO, { capabilities: {} });
      await client.connect(transport);
      const tools = await client.listTools();
      this.clients.set(key, client);
      this.transports.set(key, transport);
      const status: MountStatus = { name, environment, ok: true, toolCount: tools.tools.length };
      this.statuses.set(key, status);
      return status;
    } catch (cause) {
      const status: MountStatus = {
        name,
        environment,
        ok: false,
        error: cause instanceof Error ? cause.message : String(cause),
      };
      this.statuses.set(key, status);
      return status;
    }
  }

  private createTransport(spec: UpstreamSpec, environment: string | undefined): Transport {
    const overlay = environment === undefined ? {} : (this.config.env?.[environment] ?? {});
    if (isHttpUpstream(spec)) {
      const headers = resolveEnvReferences({ ...(spec.headers ?? {}) });
      return new StreamableHTTPClientTransport(new URL(spec.url), {
        requestInit: Object.keys(headers).length > 0 ? { headers } : {},
      });
    }
    const env = resolveEnvReferences({ ...(spec.env ?? {}), ...overlay });
    return new StdioClientTransport({
      command: spec.command,
      args: spec.args ?? [],
      env: { ...inheritedEnvironment(), ...env },
      ...(spec.cwd ? { cwd: spec.cwd } : {}),
      stderr: "inherit",
    });
  }

  async listTools(name: string, environment: string | undefined): Promise<ListToolsResult> {
    const client = await this.client(name, environment);
    return client.listTools();
  }

  async callTool(
    name: string,
    environment: string | undefined,
    toolName: string,
    args: Record<string, unknown>,
  ): Promise<CallToolResult> {
    const client = await this.client(name, environment);
    return (await client.callTool({ name: toolName, arguments: args })) as CallToolResult;
  }

  async close(): Promise<void> {
    for (const [key, client] of this.clients) {
      try {
        await client.close();
      } catch (cause) {
        // Shutdown must reach every upstream, so a close failure is reported
        // and the loop continues rather than aborting the remaining closes.
        process.stderr.write(`kido-mcp-gateway: closing ${key} failed: ${String(cause)}\n`);
      }
    }
    this.clients.clear();
    this.transports.clear();
  }
}

/** PATH and friends, so `npx`-style upstream commands resolve. */
function inheritedEnvironment(): Record<string, string> {
  const inherited: Record<string, string> = {};
  for (const key of ["PATH", "HOME", "SHELL", "TERM", "USER", "TMPDIR", "LANG", "NODE_PATH"]) {
    const value = process.env[key];
    if (value !== undefined) inherited[key] = value;
  }
  return inherited;
}
