/**
 * The `verify_ui_against_figma` composite tool.
 *
 * This is the shape of tool native per-project MCP config cannot express: one
 * call that spans two upstream design-QA tools and the Playwright run's own
 * output, returning a single verdict instead of three fragments the agent has
 * to re-assemble.
 */

import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

import { type CompositeVerifyUiConfig, parseExportEntry } from "./config.js";
import type { MountRegistry } from "./upstream.js";

export const VERIFY_UI_TOOL_NAME = "verify_ui_against_figma";

export function verifyUiToolDefinition(environments: string[]) {
  const properties: Record<string, object> = {
    nodeId: {
      type: "string",
      description: "Figma node id to verify against, e.g. \"12077:253458\".",
    },
    url: {
      type: "string",
      description: "URL of the rendered page Playwright exercised.",
    },
  };
  if (environments.length > 0) {
    properties["environment"] = {
      type: "string",
      enum: environments,
      description: `Connection environment. One of: ${environments.join(", ")}.`,
    };
  }
  return {
    name: VERIFY_UI_TOOL_NAME,
    description:
      "Verify a rendered UI against its Figma node: pulls the design spec and the DOM diff " +
      "from the design-QA upstream, folds in the Playwright report, and returns one verdict.",
    inputSchema: {
      type: "object" as const,
      properties,
      required: ["nodeId", "url"],
    },
  };
}

/** Text a tool result carries, flattened for embedding in the composite verdict. */
function resultText(result: CallToolResult): string {
  return result.content
    .map((block) => (block.type === "text" ? block.text : `[${block.type}]`))
    .join("\n");
}

async function readPlaywrightReport(path: string): Promise<{ ok: boolean; summary: string }> {
  const { readFile } = await import("node:fs/promises");
  let raw: string;
  try {
    raw = await readFile(path, "utf8");
  } catch (cause) {
    // A missing report is a real finding, not a crash: the caller learns the
    // UI was never exercised rather than getting a false pass.
    return { ok: false, summary: `Playwright report unreadable at ${path}: ${String(cause)}` };
  }
  try {
    const parsed = JSON.parse(raw) as { stats?: { expected?: number; unexpected?: number; flaky?: number } };
    const stats = parsed.stats ?? {};
    const failed = stats.unexpected ?? 0;
    return {
      ok: failed === 0,
      summary: `Playwright: ${stats.expected ?? 0} passed, ${failed} failed, ${stats.flaky ?? 0} flaky`,
    };
  } catch (cause) {
    return { ok: false, summary: `Playwright report at ${path} is not valid JSON: ${String(cause)}` };
  }
}

export async function runVerifyUiAgainstFigma(
  registry: MountRegistry,
  composite: CompositeVerifyUiConfig,
  args: Record<string, unknown>,
  environment: string | undefined,
): Promise<CallToolResult> {
  const nodeId = args["nodeId"];
  const url = args["url"];
  if (typeof nodeId !== "string" || typeof url !== "string") {
    return {
      isError: true,
      content: [{ type: "text", text: "verify_ui_against_figma requires string \"nodeId\" and \"url\" arguments" }],
    };
  }

  const spec = parseExportEntry(composite.figmaSpecTool);
  const compare = parseExportEntry(composite.domCompareTool);

  const specResult = await registry.callTool(spec.mount, environment, spec.tool, { nodeId });
  const compareResult = await registry.callTool(compare.mount, environment, compare.tool, { nodeId, url });
  const playwright = await readPlaywrightReport(composite.playwrightReport);

  const failed = specResult.isError === true || compareResult.isError === true || !playwright.ok;
  const verdict = failed ? "FAIL" : "PASS";

  return {
    isError: failed,
    content: [
      {
        type: "text",
        text: [
          `verify_ui_against_figma: ${verdict} (node ${nodeId} @ ${url})`,
          `--- ${composite.figmaSpecTool} ---`,
          resultText(specResult),
          `--- ${composite.domCompareTool} ---`,
          resultText(compareResult),
          `--- playwright ---`,
          playwright.summary,
        ].join("\n"),
      },
    ],
  };
}
