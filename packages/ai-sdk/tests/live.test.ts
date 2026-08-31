import { describe, expect, it } from "vitest";

import {
  PREFERRED_TOOL_NAME,
  flattenToolResult,
  getWebzTools,
  webzNewsSearch,
} from "../src/index.js";

const hasToken = Boolean(process.env.WEBZ_API_TOKEN?.trim());

describe.skipIf(!hasToken)("live hosted MCP", () => {
  it("loads tools from tools/list", async () => {
    const session = await getWebzTools();
    try {
      expect(PREFERRED_TOOL_NAME in session.tools).toBe(true);
    } finally {
      await session.close();
    }
  });

  it("calls news search on the hosted server", async () => {
    const session = await webzNewsSearch();
    try {
      const result = await session.client.callTool({
        name: session.toolName,
        arguments: { query: "AI regulation Europe", k: 1 },
      });
      const text = flattenToolResult(result);
      expect(text).toContain("Query:");
      expect(text.trim().length).toBeGreaterThan(0);
    } finally {
      await session.close();
    }
  });
});
