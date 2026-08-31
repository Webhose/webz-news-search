/**
 * direct News Search through the AI SDK MCP wrapper.
 *
 * usage:
 *   cp .env.example .env
 *   npx tsx examples/run-news-search.ts
 *
 * optional: export WEBZ_API_TOKEN instead of using .env
 */

import { loadLocalEnv } from "./load-env.js";

loadLocalEnv();

import {
  flattenToolResult,
  webzNewsSearch,
} from "../src/index.js";
import { printLiveToolSchema } from "./print-tool-schema.js";

const QUERY = "How many goals does Cristiano have and how many left to 1000?";

async function main(): Promise<void> {
  const session = await webzNewsSearch();
  try {
    printLiveToolSchema(session.tools, session.toolName);
    console.log("---");
    const result = await session.client.callTool({
      name: session.toolName,
      arguments: { query: QUERY, k: 3 },
    });
    console.log(flattenToolResult(result));
    console.log();
    console.log("SUCCESS ! End of tool");
  } finally {
    await session.close();
  }
}

main().catch((error: unknown) => {
  console.error("search failed:", error);
  process.exitCode = 1;
});
