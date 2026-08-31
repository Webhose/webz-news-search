import { createMCPClient } from "@ai-sdk/mcp";

import {
  DEFAULT_MCP_URL,
  MCP_URL_ENV_NAME,
  PREFERRED_TOOL_NAME,
  TOKEN_ENV_NAME,
} from "./consts.js";

type McpClient = Awaited<ReturnType<typeof createMCPClient>>;
type McpToolSet = Awaited<ReturnType<McpClient["tools"]>>;

export class WebzConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WebzConfigError";
  }
}

export type WebzClientOptions = {
  apiToken?: string;
  mcpUrl?: string;
};

export type WebzToolMap = Record<string, unknown>;

export type WebzToolsSession<T extends WebzToolMap = McpToolSet> = {
  client: McpClient;
  tools: T;
  close: () => Promise<void>;
};

export type WebzNewsSearchSession<T extends WebzToolMap = McpToolSet> =
  WebzToolsSession<T> & {
    tool: T[string];
    toolName: string;
  };

export function resolveApiToken(apiToken?: string): string {
  const token = (apiToken ?? process.env[TOKEN_ENV_NAME] ?? "").trim();
  if (!token) {
    throw new WebzConfigError(
      `missing Webz API token. set ${TOKEN_ENV_NAME} or pass apiToken.`,
    );
  }
  return token;
}

export function resolveMcpUrl(mcpUrl?: string): string {
  const url = (mcpUrl ?? process.env[MCP_URL_ENV_NAME] ?? DEFAULT_MCP_URL).trim();
  if (!url) {
    throw new WebzConfigError("missing MCP url.");
  }
  return url.replace(/\/+$/, "");
}

export function buildMcpHeaders(apiToken: string): Record<string, string> {
  return { Authorization: `Bearer ${apiToken}` };
}

export function pickNewsSearchTool<T extends WebzToolMap>(
  tools: T,
): { name: string; tool: T[string] } {
  const names = Object.keys(tools);
  if (names.length === 0) {
    throw new WebzConfigError("MCP server returned no tools.");
  }
  if (PREFERRED_TOOL_NAME in tools) {
    return {
      name: PREFERRED_TOOL_NAME,
      tool: tools[PREFERRED_TOOL_NAME] as T[string],
    };
  }
  if (names.length === 1) {
    const name = names[0];
    return { name, tool: tools[name] as T[string] };
  }
  throw new WebzConfigError(
    `MCP server did not expose ${PREFERRED_TOOL_NAME}. available tools: ${names.join(", ")}`,
  );
}

export function flattenToolResult(result: unknown): string {
  if (typeof result === "string") {
    return result;
  }
  if (Array.isArray(result)) {
    return result
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "text" in item) {
          return String((item as { text?: unknown }).text ?? "");
        }
        return "";
      })
      .filter(Boolean)
      .join("\n");
  }
  if (result && typeof result === "object") {
    const payload = result as { content?: unknown; text?: unknown };
    if (payload.content !== undefined) {
      return flattenToolResult(payload.content);
    }
    if (typeof payload.text === "string") {
      return payload.text;
    }
  }
  return String(result);
}

export async function createWebzClient(options: WebzClientOptions = {}) {
  const token = resolveApiToken(options.apiToken);
  const url = resolveMcpUrl(options.mcpUrl);
  return createMCPClient({
    transport: {
      type: "http",
      url,
      headers: buildMcpHeaders(token),
    },
  });
}

export async function getWebzTools<T extends WebzToolMap = WebzToolMap>(
  options: WebzClientOptions = {},
): Promise<WebzToolsSession<T>> {
  const client = await createWebzClient(options);
  // ponytail: schemas come from MCP tools/list; new filters ship with the server, not this package
  const tools = (await client.tools()) as T;
  if (!tools || Object.keys(tools).length === 0) {
    await client.close();
    throw new WebzConfigError("MCP server returned no tools.");
  }
  return {
    client,
    tools,
    close: () => client.close(),
  };
}

export async function webzNewsSearch<T extends WebzToolMap = WebzToolMap>(
  options: WebzClientOptions = {},
): Promise<WebzNewsSearchSession<T>> {
  const session = await getWebzTools<T>(options);
  const picked = pickNewsSearchTool(session.tools);
  return {
    ...session,
    tool: picked.tool,
    toolName: picked.name,
  };
}
