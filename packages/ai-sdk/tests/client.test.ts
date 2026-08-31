import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createMCPClient } from "@ai-sdk/mcp";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_MCP_URL,
  PREFERRED_TOOL_NAME,
  TOKEN_ENV_NAME,
  WebzConfigError,
  buildMcpHeaders,
  flattenToolResult,
  getWebzTools,
  pickNewsSearchTool,
  resolveApiToken,
  resolveMcpUrl,
  webzNewsSearch,
} from "../src/index.js";

vi.mock("@ai-sdk/mcp", () => ({
  createMCPClient: vi.fn(),
}));

const createMCPClientMock = vi.mocked(createMCPClient);

const PACKAGE_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CLIENT_SOURCE = readFileSync(join(PACKAGE_ROOT, "src", "client.ts"), "utf8");
const CONSTS_SOURCE = readFileSync(join(PACKAGE_ROOT, "src", "consts.ts"), "utf8");

const FILTER_NAMES_OWNED_BY_MCP = [
  "allow_all_dates",
  "exclude_domain",
  "domain_rank_gte",
  "domain_rank_lte",
  "trust_category",
  "political_bias",
  "min_similarity",
  "allow_multiple_chunks_per_article",
];

function fakeTools() {
  return {
    [PREFERRED_TOOL_NAME]: { description: "news search" },
    extra_tool: { description: "other" },
  };
}

function mockClient(tools: Record<string, unknown> = fakeTools()) {
  const toolsFn = vi.fn().mockResolvedValue(tools);
  const close = vi.fn().mockResolvedValue(undefined);
  const client = { tools: toolsFn, close };
  createMCPClientMock.mockResolvedValue(client as never);
  return { client, toolsFn, close };
}

afterEach(() => {
  vi.clearAllMocks();
  delete process.env[TOKEN_ENV_NAME];
  delete process.env.WEBZ_MCP_URL;
});

describe("config", () => {
  it("requires an api token", () => {
    expect(() => resolveApiToken()).toThrow(/missing Webz API token/);
  });

  it("prefers an explicit token over the environment", () => {
    process.env[TOKEN_ENV_NAME] = "from-env";
    expect(resolveApiToken(" from-arg ")).toBe("from-arg");
  });

  it("uses the hosted MCP url by default", () => {
    expect(resolveMcpUrl()).toBe(DEFAULT_MCP_URL);
    expect(resolveMcpUrl("https://localhost:8765/mcp/")).toBe(
      "https://localhost:8765/mcp",
    );
  });

  it("builds a bearer header", () => {
    expect(buildMcpHeaders("secret-token")).toEqual({
      Authorization: "Bearer secret-token",
    });
  });
});

describe("pickNewsSearchTool", () => {
  it("prefers the named news search tool", () => {
    const tools = fakeTools();
    expect(pickNewsSearchTool(tools)).toEqual({
      name: PREFERRED_TOOL_NAME,
      tool: tools[PREFERRED_TOOL_NAME],
    });
  });

  it("falls back to a single tool", () => {
    const only = { whatever_the_server_exposes: { description: "x" } };
    expect(pickNewsSearchTool(only)).toEqual({
      name: "whatever_the_server_exposes",
      tool: only.whatever_the_server_exposes,
    });
  });

  it("errors when the preferred tool is missing among many", () => {
    expect(() =>
      pickNewsSearchTool({ alpha: {}, beta: {} }),
    ).toThrow(WebzConfigError);
  });
});

describe("getWebzTools", () => {
  it("loads whatever MCP tools() returns without hardcoded schemas", async () => {
    const { client, toolsFn } = mockClient();
    const session = await getWebzTools({
      apiToken: "tok",
      mcpUrl: "https://example.test/mcp",
    });

    expect(createMCPClientMock).toHaveBeenCalledWith({
      transport: {
        type: "http",
        url: "https://example.test/mcp",
        headers: { Authorization: "Bearer tok" },
      },
    });
    expect(toolsFn).toHaveBeenCalledTimes(1);
    expect(toolsFn.mock.calls[0] ?? []).toEqual([]);
    expect(Object.keys(session.tools)).toEqual([
      PREFERRED_TOOL_NAME,
      "extra_tool",
    ]);
    expect(session.client).toBe(client);
  });

  it("rejects an empty tool list", async () => {
    mockClient({});
    await expect(getWebzTools({ apiToken: "tok" })).rejects.toThrow(
      /returned no tools/,
    );
  });
});

describe("webzNewsSearch", () => {
  it("returns the live news search tool from MCP", async () => {
    const tools = fakeTools();
    mockClient(tools);
    const session = await webzNewsSearch({ apiToken: "tok" });
    expect(session.toolName).toBe(PREFERRED_TOOL_NAME);
    expect(session.tool).toBe(tools[PREFERRED_TOOL_NAME]);
  });
});

describe("flattenToolResult", () => {
  it("unwraps MCP text content blocks", () => {
    const blocks = [
      { type: "text", text: "Query: AI regulation Europe\nTitle: Example" },
    ];
    expect(flattenToolResult(blocks)).toBe(
      "Query: AI regulation Europe\nTitle: Example",
    );
    expect(flattenToolResult({ content: blocks })).toBe(
      "Query: AI regulation Europe\nTitle: Example",
    );
    expect(flattenToolResult("already text")).toBe("already text");
  });
});

describe("wrapper source", () => {
  it("does not hardcode MCP filter fields", () => {
    const combined = CLIENT_SOURCE + CONSTS_SOURCE;
    for (const name of FILTER_NAMES_OWNED_BY_MCP) {
      expect(combined, `wrapper must not hardcode MCP filter ${name}`).not.toContain(
        name,
      );
    }
  });
});
