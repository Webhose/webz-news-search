/**
 * Mastra agent example using live Webz MCP tools.
 *
 * usage:
 *   cp .env.example .env
 *   npx tsx examples/run-agent.ts
 *
 * optional: export WEBZ_API_TOKEN / OPENAI_API_KEY instead of using .env
 */

import { loadLocalEnv } from "./load-env.js";

loadLocalEnv();

import { Agent } from "@mastra/core/agent";

import { PREFERRED_TOOL_NAME } from "../src/consts.js";
import { getWebzTools } from "../src/index.js";
import { printLiveToolSchema } from "./print-tool-schema.js";

const SYSTEM_PROMPT =
  "You are a news research assistant. " +
  `Always call the ${PREFERRED_TOOL_NAME} tool before answering. ` +
  "Pass a plain-language query and k between 3 and 10. " +
  "Do not invent facts. Answer only from tool output and cite article titles and URLs.";

const PROMPT =
  `Call ${PREFERRED_TOOL_NAME} once with query "Donald Trump USA", k=5, days=7. ` +
  "After you receive the tool results, write a short summary with article titles and URLs. Do not call the tool again.";

async function main(): Promise<void> {
  if (!process.env.OPENAI_API_KEY?.trim()) {
    throw new Error("set OPENAI_API_KEY to run the Mastra agent example.");
  }

  const { tools, close } = await getWebzTools();
  try {
    printLiveToolSchema(tools);
    console.log("---");
    const agent = new Agent({
      id: "webz-news-agent",
      name: "Webz News Agent",
      instructions: SYSTEM_PROMPT,
      model: "openai/gpt-4.1-mini",
      tools,
    });
    const result = await agent.generate(PROMPT);
    console.log(result.text);
  } finally {
    await close();
  }
}

main().catch((error: unknown) => {
  console.error("agent failed:", error);
  process.exitCode = 1;
});
