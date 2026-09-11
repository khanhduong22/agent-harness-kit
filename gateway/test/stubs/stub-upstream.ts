/**
 * A trivial local MCP server used as a real upstream in the integration tests.
 *
 * Run as `node dist/test/stubs/stub-upstream.js <name>`. It answers over stdio
 * like any other MCP server, so the gateway spawns and speaks to it exactly as
 * it would to `npx -y framefit` — no network, no mocks inside the gateway.
 *
 * Every tool result names the stub and the value of TARGET_ENV, which is how the
 * tests prove both *which* upstream answered and *which* environment's
 * connection was used.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type CallToolResult,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";

const stubName = process.argv[2] ?? "stub";

/** Tools every stub offers, so `export` filtering has something to filter out. */
const NOISE_TOOLS = ["noise_one", "noise_two", "noise_three", "noise_four", "noise_five"];

const tools: Tool[] = [
  {
    name: "ping",
    description: `Answer with the stub's own name (${stubName}).`,
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get_layout_spec",
    description: "Stand-in for the design-QA upstream's layout spec tool.",
    inputSchema: { type: "object", properties: { nodeId: { type: "string" } } },
  },
  {
    name: "compare_node_to_dom",
    description: "Stand-in for the design-QA upstream's DOM comparison tool.",
    inputSchema: {
      type: "object",
      properties: { nodeId: { type: "string" }, url: { type: "string" } },
    },
  },
  ...NOISE_TOOLS.map((name) => ({
    name,
    description: "Unexported noise; must never appear in the gateway's tools/list.",
    inputSchema: { type: "object" as const, properties: {} },
  })),
];

const server = new Server({ name: stubName, version: "0.0.1" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request): Promise<CallToolResult> => {
  const args = (request.params.arguments ?? {}) as Record<string, unknown>;
  const environment = process.env["TARGET_ENV"] ?? "none";
  const suffix = `upstream=${stubName} env=${environment}`;

  switch (request.params.name) {
    case "ping":
      return { content: [{ type: "text", text: `pong ${suffix}` }] };
    case "get_layout_spec":
      return { content: [{ type: "text", text: `layout-spec node=${String(args["nodeId"])} ${suffix}` }] };
    case "compare_node_to_dom":
      return {
        content: [
          {
            type: "text",
            text: `dom-diff node=${String(args["nodeId"])} url=${String(args["url"])} ${suffix}`,
          },
        ],
      };
    default:
      return {
        isError: true,
        content: [{ type: "text", text: `stub ${stubName} has no tool ${request.params.name}` }],
      };
  }
});

await server.connect(new StdioServerTransport());
