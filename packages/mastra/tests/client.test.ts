import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { MCPClient } from "@mastra/mcp";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_MCP_URL,
  MCP_SERVER_NAME,
  PREFERRED_TOOL_NAME,
  TOKEN_ENV_NAME,
  WebzConfigError,
  buildMcpHeaders,
  callWebzTool,
  exposeServerToolNames,
  flattenToolResult,
  getWebzTools,
  pickNewsSearchTool,
  resolveApiToken,
  resolveMcpUrl,
  webzNewsSearch,
} from "../src/index.js";

vi.mock("@mastra/mcp", () => ({
  MCPClient: vi.fn(),
}));

const MCPClientMock = vi.mocked(MCPClient);

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
    [PREFERRED_TOOL_NAME]: {
      id: `${MCP_SERVER_NAME}_${PREFERRED_TOOL_NAME}`,
      description: "news search",
      execute: vi.fn(),
    },
    extra_tool: {
      id: `${MCP_SERVER_NAME}_extra_tool`,
      description: "other",
      execute: vi.fn(),
    },
  };
}

function mockClient(
  tools: Record<string, { id: string; description: string; execute: ReturnType<typeof vi.fn> }> = fakeTools(),
  errors: Record<string, string> = {},
) {
  const listToolsetsWithErrors = vi.fn().mockResolvedValue({
    toolsets: { [MCP_SERVER_NAME]: tools },
    errors,
  });
  const disconnect = vi.fn().mockResolvedValue(undefined);
  const client = { listToolsetsWithErrors, disconnect };
  MCPClientMock.mockImplementation(() => client as never);
  return { client, listToolsetsWithErrors, disconnect };
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

  it("rejects a cleartext endpoint before a client exists", () => {
    expect(() => resolveMcpUrl("http://news-search-mcp.webz.io/mcp")).toThrow(
      WebzConfigError,
    );
    expect(() => resolveMcpUrl("http://news-search-mcp.webz.io/mcp")).toThrow(
      /absolute https:\/\/ URL/,
    );
  });

  it("rejects a relative endpoint", () => {
    expect(() => resolveMcpUrl("/mcp")).toThrow(WebzConfigError);
    expect(MCPClientMock).not.toHaveBeenCalled();
  });

  it("builds a bearer header", () => {
    expect(buildMcpHeaders("secret-token")).toEqual({
      Authorization: "Bearer secret-token",
    });
  });
});

describe("exposeServerToolNames", () => {
  it("restores the hosted tool name as the Mastra tool id", () => {
    const tools = fakeTools();
    const exposed = exposeServerToolNames(tools);
    expect(exposed[PREFERRED_TOOL_NAME]?.id).toBe(PREFERRED_TOOL_NAME);
    expect(Object.keys(exposed)).toEqual([PREFERRED_TOOL_NAME, "extra_tool"]);
  });
});

describe("pickNewsSearchTool", () => {
  it("prefers the named news search tool", () => {
    const tools = exposeServerToolNames(fakeTools());
    expect(pickNewsSearchTool(tools)).toEqual({
      name: PREFERRED_TOOL_NAME,
      tool: tools[PREFERRED_TOOL_NAME],
    });
  });

  it("falls back to a single tool", () => {
    const only = exposeServerToolNames({
      whatever_the_server_exposes: {
        id: "webz_whatever_the_server_exposes",
        description: "x",
        execute: vi.fn(),
      },
    });
    expect(pickNewsSearchTool(only)).toEqual({
      name: "whatever_the_server_exposes",
      tool: only.whatever_the_server_exposes,
    });
  });

  it("errors when the preferred tool is missing among many", () => {
    expect(() =>
      pickNewsSearchTool({
        alpha: { id: "alpha", description: "", execute: vi.fn() },
        beta: { id: "beta", description: "", execute: vi.fn() },
      } as never),
    ).toThrow(WebzConfigError);
  });
});

describe("getWebzTools", () => {
  it("loads whatever the MCP server lists without hardcoded schemas", async () => {
    const tools = fakeTools();
    const { listToolsetsWithErrors, disconnect } = mockClient(tools);
    const session = await getWebzTools({
      apiToken: "tok",
      mcpUrl: "https://example.test/mcp",
    });

    expect(MCPClientMock).toHaveBeenCalledTimes(1);
    const config = MCPClientMock.mock.calls[0]?.[0];
    const server = config?.servers[MCP_SERVER_NAME];
    const serverUrl = server && "url" in server ? server.url : undefined;
    expect(serverUrl?.href).toBe("https://example.test/mcp");
    expect(server && "requestInit" in server ? server.requestInit : {}).toEqual({
      headers: { Authorization: "Bearer tok" },
    });
    expect(server && "allowedHosts" in server ? server.allowedHosts : []).toEqual([
      "example.test",
    ]);
    expect(listToolsetsWithErrors).toHaveBeenCalledTimes(1);
    expect(Object.keys(session.tools)).toEqual([PREFERRED_TOOL_NAME, "extra_tool"]);
    expect(session.tools[PREFERRED_TOOL_NAME]?.id).toBe(PREFERRED_TOOL_NAME);
    expect(disconnect).not.toHaveBeenCalled();
    await session.close();
    expect(disconnect).toHaveBeenCalledTimes(1);
  });

  it("does not construct a client for a cleartext endpoint", async () => {
    mockClient();
    await expect(
      getWebzTools({ apiToken: "tok", mcpUrl: "http://example.test/mcp" }),
    ).rejects.toThrow(/absolute https:\/\/ URL/);
    expect(MCPClientMock).not.toHaveBeenCalled();
  });

  it("rejects an empty tool list and closes the client", async () => {
    const { disconnect } = mockClient({});
    await expect(getWebzTools({ apiToken: "tok" })).rejects.toThrow(
      /returned no tools/,
    );
    expect(disconnect).toHaveBeenCalledTimes(1);
  });

  it("surfaces a server connection error and closes the client", async () => {
    const { disconnect } = mockClient({}, { [MCP_SERVER_NAME]: "connection refused" });
    await expect(getWebzTools({ apiToken: "tok" })).rejects.toThrow(
      /connection refused/,
    );
    expect(disconnect).toHaveBeenCalledTimes(1);
  });
});

describe("webzNewsSearch", () => {
  it("returns the live news search tool from MCP", async () => {
    const tools = fakeTools();
    mockClient(tools);
    const session = await webzNewsSearch({ apiToken: "tok" });
    expect(session.toolName).toBe(PREFERRED_TOOL_NAME);
    expect(session.tool).toBe(tools[PREFERRED_TOOL_NAME]);
    expect(session.tool.id).toBe(PREFERRED_TOOL_NAME);
  });
});

describe("callWebzTool", () => {
  it("invokes the Mastra tool without an agent context", async () => {
    const execute = vi.fn().mockResolvedValue({
      content: [{ type: "text", text: "Query: hi" }],
    });
    const result = await callWebzTool(
      { id: PREFERRED_TOOL_NAME, description: "news", execute } as never,
      { query: "hi" },
    );
    expect(execute).toHaveBeenCalledWith({ query: "hi" });
    expect(flattenToolResult(result)).toBe("Query: hi");
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
    expect(flattenToolResult({ result: "Query: AI regulation Europe" })).toBe(
      "Query: AI regulation Europe",
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
