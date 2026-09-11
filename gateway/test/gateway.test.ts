/**
 * Integration tests for the gateway.
 *
 * Every test mounts real stub MCP servers as child processes over stdio and
 * drives the gateway through a real MCP client, so what is exercised is the
 * whole path: client -> gateway -> spawned upstream -> back.
 */

import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import type { CallToolResult, ListToolsResult } from "@modelcontextprotocol/sdk/types.js";

import type { GatewayConfig, UpstreamSpec } from "../src/config.js";
import { GATEWAY_STATUS_TOOL, MOUNTS_META_KEY, createGateway } from "../src/gateway.js";
import type { MountStatus } from "../src/upstream.js";

const execFileAsync = promisify(execFile);

const here = fileURLToPath(new URL(".", import.meta.url));
const STUB = join(here, "stubs", "stub-upstream.js");
const CLI = join(here, "..", "src", "cli.js");

/** A stub upstream, spawned exactly like any real stdio MCP server. */
function stub(name: string): UpstreamSpec {
  return { command: process.execPath, args: [STUB, name] };
}

/** An upstream that cannot start, for the failure-reporting scenarios. */
function brokenUpstream(): UpstreamSpec {
  return { command: process.execPath, args: ["-e", "process.exit(7)"] };
}

const openGateways: Array<{ close: () => Promise<void> }> = [];

async function connect(config: GatewayConfig): Promise<Client> {
  const gateway = createGateway(config);
  openGateways.push(gateway);
  const client = new Client({ name: "test-client", version: "0.0.1" }, { capabilities: {} });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await Promise.all([gateway.server.connect(serverTransport), client.connect(clientTransport)]);
  return client;
}

function text(result: CallToolResult): string {
  return result.content.map((block) => (block.type === "text" ? block.text : "")).join("\n");
}

function mounts(result: ListToolsResult): MountStatus[] {
  return (result._meta?.[MOUNTS_META_KEY] ?? []) as MountStatus[];
}

after(async () => {
  for (const gateway of openGateways) await gateway.close();
});

describe("gateway re-exports a curated subset of mounted upstreams", () => {
  const config: GatewayConfig = {
    mount: { alpha: stub("alpha"), beta: stub("beta") },
    export: ["alpha:ping", "beta:ping", "alpha:get_layout_spec"],
  };

  it("returns only the exported tools, and no upstream noise", async () => {
    const client = await connect(config);
    const listed = await client.listTools();
    const names = listed.tools.map((tool) => tool.name).sort();

    assert.deepEqual(names, [
      GATEWAY_STATUS_TOOL,
      "alpha__get_layout_spec",
      "alpha__ping",
      "beta__ping",
    ].sort());

    // Both stubs offer eight tools each; only three are exported.
    for (const noise of ["noise_one", "alpha__noise_one", "beta__compare_node_to_dom"]) {
      assert.ok(!names.includes(noise), `${noise} must not be re-exported`);
    }
  });

  it("routes a call to the upstream that owns the tool", async () => {
    const client = await connect(config);

    const fromAlpha = (await client.callTool({ name: "alpha__ping" })) as CallToolResult;
    const fromBeta = (await client.callTool({ name: "beta__ping" })) as CallToolResult;

    // Both stubs expose a tool called `ping`, so the upstream marker in the
    // result is the only thing that can tell the two routes apart.
    assert.match(text(fromAlpha), /upstream=alpha/);
    assert.match(text(fromBeta), /upstream=beta/);
    assert.ok(!text(fromAlpha).includes("upstream=beta"));
  });

  it("returns the upstream's result unmodified", async () => {
    const client = await connect(config);
    const result = (await client.callTool({
      name: "alpha__get_layout_spec",
      arguments: { nodeId: "12077:253458" },
    })) as CallToolResult;

    assert.deepEqual(result.content, [
      { type: "text", text: "layout-spec node=12077:253458 upstream=alpha env=none" },
    ]);
  });
});

describe("an upstream failure is reported, not masked", () => {
  const config: GatewayConfig = {
    mount: { alpha: stub("alpha"), wreck: brokenUpstream() },
    export: ["alpha:ping", "wreck:ping"],
  };

  it("reports the failed mount on tools/list while healthy tools stay callable", async () => {
    const client = await connect(config);
    const listed = await client.listTools();

    const wreck = mounts(listed).find((status) => status.name === "wreck");
    assert.ok(wreck, "the failed mount must appear in the tools/list report");
    assert.equal(wreck.ok, false);
    assert.ok(wreck.error && wreck.error.length > 0, "the failure must carry its error");

    const alpha = mounts(listed).find((status) => status.name === "alpha");
    assert.equal(alpha?.ok, true);

    const healthy = (await client.callTool({ name: "alpha__ping" })) as CallToolResult;
    assert.match(text(healthy), /upstream=alpha/);
    assert.notEqual(healthy.isError, true);
  });

  it("reports ok and failed mounts through gateway_status", async () => {
    const client = await connect(config);
    const status = (await client.callTool({ name: GATEWAY_STATUS_TOOL })) as CallToolResult;

    assert.equal(status.isError, true);
    assert.match(text(status), /ok {6}alpha/);
    assert.match(text(status), /FAILED {2}wreck/);
  });
});

describe("environment is a parameter, not three registrations", () => {
  const config: GatewayConfig = {
    mount: { alpha: stub("alpha") },
    export: ["alpha:ping"],
    env: {
      local: { TARGET_ENV: "local" },
      dev: { TARGET_ENV: "dev" },
      staging: { TARGET_ENV: "staging" },
    },
  };

  it("exposes one tool carrying an environment enum of every configured environment", async () => {
    const client = await connect(config);
    const listed = await client.listTools();
    const pings = listed.tools.filter((tool) => tool.name.endsWith("ping"));

    assert.equal(pings.length, 1, "one tool per capability, not one per environment");
    const environment = pings[0]?.inputSchema.properties?.["environment"] as { enum?: string[] };
    assert.deepEqual(environment.enum, ["local", "dev", "staging"]);
  });

  it("uses the staging connection when the parameter says staging", async () => {
    const client = await connect(config);

    const staging = (await client.callTool({
      name: "alpha__ping",
      arguments: { environment: "staging" },
    })) as CallToolResult;
    const dev = (await client.callTool({
      name: "alpha__ping",
      arguments: { environment: "dev" },
    })) as CallToolResult;

    assert.match(text(staging), /env=staging/);
    assert.match(text(dev), /env=dev/);
  });

  it("defaults to the first configured environment when none is given", async () => {
    const client = await connect(config);
    const result = (await client.callTool({ name: "alpha__ping" })) as CallToolResult;
    assert.match(text(result), /env=local/);
  });

  it("refuses an unknown environment, naming the configured ones, without calling upstream", async () => {
    const gateway = createGateway(config);
    openGateways.push(gateway);
    const client = new Client({ name: "test-client", version: "0.0.1" }, { capabilities: {} });
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
    await Promise.all([gateway.server.connect(serverTransport), client.connect(clientTransport)]);

    const result = (await client.callTool({
      name: "alpha__ping",
      arguments: { environment: "production" },
    })) as CallToolResult;

    assert.equal(result.isError, true);
    assert.match(text(result), /unknown environment "production"/);
    assert.match(text(result), /local, dev, staging/);
    // Nothing was mounted, so no upstream was contacted at all.
    assert.deepEqual(gateway.status(), []);
  });
});

describe("composite tool spans two upstream tools and the Playwright report", () => {
  async function configWithReport(stats: object): Promise<GatewayConfig> {
    const dir = await mkdtemp(join(tmpdir(), "kido-gateway-"));
    const report = join(dir, "playwright-report.json");
    await writeFile(report, JSON.stringify({ stats }), "utf8");
    return {
      mount: { framefit: stub("framefit") },
      export: ["framefit:get_layout_spec"],
      composite: {
        verify_ui_against_figma: {
          figmaSpecTool: "framefit:get_layout_spec",
          domCompareTool: "framefit:compare_node_to_dom",
          playwrightReport: report,
        },
      },
    };
  }

  it("passes when both design-QA tools and Playwright agree", async () => {
    const client = await connect(await configWithReport({ expected: 4, unexpected: 0, flaky: 0 }));
    const listed = await client.listTools();
    assert.ok(listed.tools.some((tool) => tool.name === "verify_ui_against_figma"));

    const result = (await client.callTool({
      name: "verify_ui_against_figma",
      arguments: { nodeId: "12077:253458", url: "http://localhost:3000/login" },
    })) as CallToolResult;

    const output = text(result);
    assert.match(output, /verify_ui_against_figma: PASS/);
    assert.match(output, /layout-spec node=12077:253458 upstream=framefit/);
    assert.match(output, /dom-diff node=12077:253458 url=http:\/\/localhost:3000\/login/);
    assert.match(output, /Playwright: 4 passed, 0 failed/);
    assert.notEqual(result.isError, true);
  });

  it("fails when the Playwright report has failures", async () => {
    const client = await connect(await configWithReport({ expected: 3, unexpected: 1, flaky: 0 }));
    const result = (await client.callTool({
      name: "verify_ui_against_figma",
      arguments: { nodeId: "12077:253458", url: "http://localhost:3000/login" },
    })) as CallToolResult;

    assert.equal(result.isError, true);
    assert.match(text(result), /verify_ui_against_figma: FAIL/);
    assert.match(text(result), /Playwright: 3 passed, 1 failed/);
  });
});

describe("status command", () => {
  async function writeConfig(config: GatewayConfig): Promise<string> {
    const dir = await mkdtemp(join(tmpdir(), "kido-gateway-cli-"));
    const path = join(dir, "gateway.config.json");
    await writeFile(path, JSON.stringify(config), "utf8");
    return path;
  }

  it("exits zero and reports ok when every mount is healthy", async () => {
    const path = await writeConfig({
      mount: { alpha: stub("alpha"), beta: stub("beta") },
      export: ["alpha:ping"],
    });

    const { stdout } = await execFileAsync(process.execPath, [CLI, "status", "--config", path]);
    assert.match(stdout, /ok {6}alpha \(8 tools\)/);
    assert.match(stdout, /ok {6}beta \(8 tools\)/);
  });

  it("exits non-zero and names the failure when a mount is broken", async () => {
    const path = await writeConfig({
      mount: { alpha: stub("alpha"), wreck: brokenUpstream() },
      export: ["alpha:ping"],
    });

    const failure = await execFileAsync(process.execPath, [CLI, "status", "--config", path]).then(
      () => undefined,
      (error: Error & { code?: number; stdout?: string }) => error,
    );

    assert.ok(failure, "status must exit non-zero when any mount failed");
    assert.equal(failure.code, 1);
    assert.match(failure.stdout ?? "", /ok {6}alpha/);
    assert.match(failure.stdout ?? "", /FAILED {2}wreck/);
  });
});
