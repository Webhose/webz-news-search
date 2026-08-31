import { PREFERRED_TOOL_NAME } from "../src/consts.js";

type McpToolShape = {
  description?: string;
  title?: string;
  inputSchema?: {
    jsonSchema?: {
      properties?: Record<string, unknown>;
    };
  };
};

export function listToolArgNames(tool: unknown): string[] {
  const properties =
    (tool as McpToolShape).inputSchema?.jsonSchema?.properties ?? {};
  return Object.keys(properties).sort();
}

export function printLiveToolSchema(
  tools: Record<string, unknown>,
  toolName: string = PREFERRED_TOOL_NAME,
): void {
  const tool = tools[toolName] as McpToolShape | undefined;
  if (!tool) {
    console.log("tool not found:", toolName);
    console.log("available tools:", Object.keys(tools).sort().join(", "));
    return;
  }

  console.log("tool name:", toolName);
  if (tool.title) {
    console.log("tool title:", tool.title);
  }
  if (tool.description?.trim()) {
    console.log("tool description:");
    console.log(tool.description.trim());
  }
  console.log(
    "live args from MCP tools/list:",
    listToolArgNames(tool).join(", "),
  );
}
