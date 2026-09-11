#!/usr/bin/env node
/**
 * `kido-mcp-gateway serve|status --config <path>`
 *
 * `serve` is the single registration line every harness points at. `status`
 * mirrors `framefit status`: it reports each mount as ok or failed and exits
 * non-zero when any mount failed, so a broken mount is diagnosable from a shell
 * without reading logs.
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { loadConfig } from "./config.js";
import { createGateway } from "./gateway.js";
import type { MountStatus } from "./upstream.js";

const USAGE = `Usage: kido-mcp-gateway <serve|status> --config <path>

  serve    Run the gateway on stdio (the transport every harness can register).
  status   Mount every upstream, report ok/failed, exit non-zero on any failure.
`;

export function formatStatus(statuses: MountStatus[]): string {
  if (statuses.length === 0) return "no mounts configured";
  return statuses
    .map((status) => {
      const where = status.environment ? `${status.name}@${status.environment}` : status.name;
      return status.ok
        ? `ok      ${where} (${status.toolCount ?? 0} tools)`
        : `FAILED  ${where}: ${status.error ?? "unknown error"}`;
    })
    .join("\n");
}

function argValue(argv: string[], flag: string): string | undefined {
  const index = argv.indexOf(flag);
  if (index === -1) return undefined;
  return argv[index + 1];
}

export async function main(argv: string[]): Promise<number> {
  const command = argv[0];
  if (!command || command === "--help" || command === "-h") {
    process.stdout.write(USAGE);
    return command ? 0 : 1;
  }

  const configPath = argValue(argv, "--config");
  if (!configPath) {
    process.stderr.write("kido-mcp-gateway: --config <path> is required\n");
    return 1;
  }

  const config = await loadConfig(configPath);
  const gateway = createGateway(config);

  if (command === "status") {
    const statuses = await gateway.registry.mountAll();
    process.stdout.write(`${formatStatus(statuses)}\n`);
    await gateway.close();
    return statuses.some((status) => !status.ok) ? 1 : 0;
  }

  if (command === "serve") {
    await gateway.server.connect(new StdioServerTransport());
    const statuses = await gateway.registry.mountAll();
    for (const status of statuses.filter((candidate) => !candidate.ok)) {
      process.stderr.write(
        `kido-mcp-gateway: mount ${status.name} FAILED: ${status.error ?? "unknown error"}\n`,
      );
    }
    return 0;
  }

  process.stderr.write(`kido-mcp-gateway: unknown command ${JSON.stringify(command)}\n${USAGE}`);
  return 1;
}

const invokedDirectly =
  process.argv[1] !== undefined && import.meta.url === new URL(`file://${process.argv[1]}`).href;

if (invokedDirectly) {
  const code = await main(process.argv.slice(2));
  if (code !== 0 || process.argv[2] === "status") {
    process.exit(code);
  }
}
