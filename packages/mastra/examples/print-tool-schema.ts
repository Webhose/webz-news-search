import { PREFERRED_TOOL_NAME } from "../src/consts.js";

type JsonSchemaObject = {
  properties?: Record<string, unknown>;
};

// Mastra wraps the MCP JSON Schema in a Standard Schema object. The raw
// schema is reachable through `["~standard"].jsonSchema.input(...)`.
type MastraToolShape = {
  id?: string;
  description?: string;
  inputSchema?: {
    "~standard"?: {
      jsonSchema?: {
        input?: (options?: { target?: string }) => JsonSchemaObject;
      };
    };
    jsonSchema?: JsonSchemaObject;
    properties?: Record<string, unknown>;
  };
};

export function listToolArgNames(tool: unknown): string[] {
  const schema = (tool as MastraToolShape).inputSchema;
  const standardInput = schema?.["~standard"]?.jsonSchema?.input;
  const properties =
    (standardInput ? standardInput({ target: "draft-07" }) : undefined)
      ?.properties ??
    schema?.jsonSchema?.properties ??
    schema?.properties ??
    {};
  return Object.keys(properties).sort();
}

export function printLiveToolSchema(
  tools: Record<string, unknown>,
  toolName: string = PREFERRED_TOOL_NAME,
): void {
  const tool = tools[toolName] as MastraToolShape | undefined;
  if (!tool) {
    console.log("tool not found:", toolName);
    console.log("available tools:", Object.keys(tools).sort().join(", "));
    return;
  }

  console.log("tool name:", tool.id ?? toolName);
  if (tool.description?.trim()) {
    console.log("tool description:");
    console.log(tool.description.trim());
  }
  const args = listToolArgNames(tool);
  if (args.length > 0) {
    console.log("live args from MCP tools/list:", args.join(", "));
  }
}
