import { describe, expect, it } from "vitest";

import {
  PREFERRED_TOOL_NAME,
  callWebzTool,
  flattenToolResult,
  webzNewsSearch,
} from "../src/index.js";

const hasToken = Boolean(process.env.WEBZ_API_TOKEN?.trim());

describe.skipIf(!hasToken)("live hosted MCP", () => {
  it("loads news_search_by_webz and calls it on the hosted server", async () => {
    const session = await webzNewsSearch();
    try {
      expect(PREFERRED_TOOL_NAME in session.tools).toBe(true);
      expect(session.toolName).toBe(PREFERRED_TOOL_NAME);
      expect(session.tool.id).toBe(PREFERRED_TOOL_NAME);
      const result = await callWebzTool(session.tool, {
        query: "AI regulation Europe",
        k: 1,
      });
      const text = flattenToolResult(result);
      expect(text).toContain("Query:");
      expect(text.trim().length).toBeGreaterThan(0);
    } finally {
      await session.close();
    }
  });
});
