import { randomUUID } from "node:crypto";

import { MCPClient } from "@mastra/mcp";

import {
  DEFAULT_MCP_URL,
  MCP_SERVER_NAME,
  MCP_URL_ENV_NAME,
  PREFERRED_TOOL_NAME,
  TOKEN_ENV_NAME,
} from "./consts.js";

type ListedTools = Awaited<
  ReturnType<MCPClient["listToolsetsWithErrors"]>
>["toolsets"][string];

export type WebzMastraTool = ListedTools[string];

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

export type WebzToolMap = Record<string, WebzMastraTool>;

export type WebzToolsSession<T extends WebzToolMap = WebzToolMap> = {
  client: MCPClient;
  tools: T;
  close: () => Promise<void>;
};

export type WebzNewsSearchSession<T extends WebzToolMap = WebzToolMap> =
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

function httpsUrlMessage(url: string): string {
  return `The Webz.io MCP endpoint must be an absolute https:// URL, got ${JSON.stringify(url)}.`;
}

export function resolveMcpUrl(mcpUrl?: string): string {
  return parseMcpUrl(mcpUrl).href;
}

function parseMcpUrl(mcpUrl?: string): URL {
  const raw = (mcpUrl ?? process.env[MCP_URL_ENV_NAME] ?? DEFAULT_MCP_URL).trim();
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new WebzConfigError(httpsUrlMessage(raw));
  }
  if (parsed.protocol !== "https:" || parsed.host.length === 0) {
    throw new WebzConfigError(httpsUrlMessage(raw));
  }
  if (parsed.pathname.length > 1) {
    parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  }
  return parsed;
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
    const payload = result as { content?: unknown; text?: unknown; result?: unknown };
    if (payload.content !== undefined) {
      return flattenToolResult(payload.content);
    }
    if (typeof payload.text === "string") {
      return payload.text;
    }
    if (typeof payload.result === "string") {
      return payload.result;
    }
  }
  return String(result);
}

/**
 * Mastra namespaces MCP tool ids as `serverName_toolName`. Agents call `tool.id`,
 * so restore the hosted server's name (`news_search_by_webz`) before returning.
 */
export function exposeServerToolNames<T extends WebzToolMap>(tools: T): T {
  const renamed = {} as T;
  for (const [name, tool] of Object.entries(tools)) {
    Object.assign(tool, { id: name });
    renamed[name as keyof T] = tool as T[keyof T];
  }
  return renamed;
}

export async function callWebzTool(
  tool: WebzMastraTool,
  input: Record<string, unknown>,
): Promise<unknown> {
  if (!tool.execute) {
    throw new WebzConfigError("MCP tool has no execute function.");
  }
  // Mastra's execute type requires an agent context. The MCP wrapper only
  // reads optional fields, and the Tool class fills the rest when context is omitted.
  const execute = tool.execute as (
    inputData: Record<string, unknown>,
    context?: unknown,
  ) => Promise<unknown>;
  return execute(input);
}

export function createWebzClient(options: WebzClientOptions = {}): MCPClient {
  const url = parseMcpUrl(options.mcpUrl);
  const token = resolveApiToken(options.apiToken);
  return new MCPClient({
    id: `webz-news-search-${randomUUID()}`,
    servers: {
      [MCP_SERVER_NAME]: {
        url,
        allowedHosts: [url.host],
        requestInit: {
          headers: buildMcpHeaders(token),
        },
      },
    },
  });
}

async function disconnectQuietly(client: MCPClient): Promise<void> {
  try {
    await client.disconnect();
  } catch {
    // The original search error is the one callers need.
  }
}

export async function getWebzTools<T extends WebzToolMap = WebzToolMap>(
  options: WebzClientOptions = {},
): Promise<WebzToolsSession<T>> {
  const client = createWebzClient(options);
  try {
    const { toolsets, errors } = await client.listToolsetsWithErrors();
    const failure = errors[MCP_SERVER_NAME];
    if (failure) {
      throw new WebzConfigError(failure);
    }
    const serverTools = (toolsets[MCP_SERVER_NAME] ?? {}) as T;
    // ponytail: schemas come from MCP tools/list; new filters ship with the server, not this package
    const tools = exposeServerToolNames(serverTools);
    if (Object.keys(tools).length === 0) {
      throw new WebzConfigError("MCP server returned no tools.");
    }
    return {
      client,
      tools,
      close: () => client.disconnect(),
    };
  } catch (error) {
    await disconnectQuietly(client);
    throw error;
  }
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
