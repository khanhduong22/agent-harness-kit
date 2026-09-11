/**
 * The gateway's configuration contract.
 *
 * Mirrors `GatewayConfig` in openspec/changes/mcp-provisioning/design.md: the
 * gateway mounts upstream servers, re-exports a curated subset of their tools,
 * and selects a connection environment by parameter.
 */

/** An upstream launched as a child process and spoken to over stdio. */
export interface StdioUpstream {
  command: string;
  args?: string[];
  /** Values may only reference secrets as `${VAR}`; never a literal. */
  env?: Record<string, string>;
  cwd?: string;
}

/** An upstream reached over streamable HTTP. */
export interface HttpUpstream {
  url: string;
  headers?: Record<string, string>;
}

export type UpstreamSpec = StdioUpstream | HttpUpstream;

export interface CompositeVerifyUiConfig {
  /** Upstream tool returning the Figma-side spec, e.g. `framefit:get_layout_spec`. */
  figmaSpecTool: string;
  /** Upstream tool diffing that spec against the rendered DOM. */
  domCompareTool: string;
  /** Path to the Playwright JSON report the composite folds into its verdict. */
  playwrightReport: string;
}

export interface GatewayConfig {
  /** Upstream servers, keyed by the name used in `export` entries. */
  mount: Record<string, UpstreamSpec>;
  /** Tools to re-export, each `"<mountName>:<upstreamToolName>"`. */
  export: string[];
  /**
   * Named connection environments (`local` | `dev` | `staging` | ...), each a
   * set of environment variables layered over the upstream's own `env`.
   * When present, exported tools gain an `environment` parameter.
   */
  env?: Record<string, Record<string, string>>;
  /** Environment used when a call omits the parameter. Defaults to the first key of `env`. */
  defaultEnvironment?: string;
  composite?: {
    verify_ui_against_figma?: CompositeVerifyUiConfig;
  };
}

export function isHttpUpstream(spec: UpstreamSpec): spec is HttpUpstream {
  return typeof (spec as HttpUpstream).url === "string";
}

/** `"framefit:get_layout_spec"` -> `{ mount: "framefit", tool: "get_layout_spec" }`. */
export function parseExportEntry(entry: string): { mount: string; tool: string } {
  const separator = entry.indexOf(":");
  if (separator <= 0 || separator === entry.length - 1) {
    throw new Error(`export entry ${JSON.stringify(entry)} must be "<mount>:<tool>"`);
  }
  return { mount: entry.slice(0, separator), tool: entry.slice(separator + 1) };
}

/**
 * The name the gateway advertises for an exported tool.
 *
 * `:` is not accepted by every MCP client's tool-name validation, so the
 * exported name uses the `server__tool` convention the kit already renders into
 * `permissions.allow` entries.
 */
export function exportedToolName(mount: string, tool: string): string {
  return `${mount}__${tool}`;
}

/** Configured environment names, in declaration order. */
export function environmentNames(config: GatewayConfig): string[] {
  return Object.keys(config.env ?? {});
}

export function defaultEnvironment(config: GatewayConfig): string | undefined {
  const names = environmentNames(config);
  if (names.length === 0) return undefined;
  if (config.defaultEnvironment) {
    if (!names.includes(config.defaultEnvironment)) {
      throw new Error(
        `defaultEnvironment ${JSON.stringify(config.defaultEnvironment)} is not one of: ${names.join(", ")}`,
      );
    }
    return config.defaultEnvironment;
  }
  return names[0];
}

/** Throws on a config the gateway cannot serve, naming the offending field. */
export function validateConfig(config: GatewayConfig): void {
  if (!config.mount || Object.keys(config.mount).length === 0) {
    throw new Error("config.mount must declare at least one upstream server");
  }
  if (!Array.isArray(config.export)) {
    throw new Error("config.export must be an array of \"<mount>:<tool>\" entries");
  }
  for (const entry of config.export) {
    const { mount } = parseExportEntry(entry);
    if (!(mount in config.mount)) {
      throw new Error(`export entry ${JSON.stringify(entry)} names unmounted server ${JSON.stringify(mount)}`);
    }
  }
  defaultEnvironment(config);
}

/** Reads and validates a JSON config file. */
export async function loadConfig(path: string): Promise<GatewayConfig> {
  const { readFile } = await import("node:fs/promises");
  const raw = await readFile(path, "utf8");
  let parsed: GatewayConfig;
  try {
    parsed = JSON.parse(raw) as GatewayConfig;
  } catch (cause) {
    throw new Error(`${path} is not valid JSON: ${(cause as Error).message}`);
  }
  validateConfig(parsed);
  return parsed;
}
