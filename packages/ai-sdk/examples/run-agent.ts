/**
 * Vercel AI SDK agent example using live Webz MCP tools.
 *
 * usage (OpenRouter):
 *   cp .env.example .env
 *   npx tsx examples/run-agent.ts
 *
 * usage (OpenAI):
 *   cp .env.example .env
 *   npx tsx examples/run-agent.ts
 *
 * optional: export WEBZ_API_TOKEN / OPENROUTER_API_KEY instead of using .env
 */

import { loadLocalEnv } from "./load-env.js";

loadLocalEnv();

import { createOpenAI } from "@ai-sdk/openai";
import { generateText, isStepCount } from "ai";

import { PREFERRED_TOOL_NAME } from "../src/consts.js";
import { getWebzTools } from "../src/index.js";
import { printLiveToolSchema } from "./print-tool-schema.js";

const OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1";
const OPENROUTER_MODEL = "openai/gpt-4o-mini";
const OPENAI_MODEL = "gpt-4.1-mini";

const SYSTEM_PROMPT =
  "You are a news research assistant. " +
  `Always call the ${PREFERRED_TOOL_NAME} tool before answering. ` +
  "Pass a plain-language query and k between 3 and 10. " +
  "Do not invent facts. Answer only from tool output and cite article titles and URLs.";

const PROMPT =
  `Call ${PREFERRED_TOOL_NAME} once with query "Donald Trump USA", k=5, days=7` +
  "After you receive the tool results, write a short summary with article titles and URLs. Do not call the tool again.";

function resolveLanguageModel() {
  const openRouterKey = process.env.OPENROUTER_API_KEY?.trim();
  if (openRouterKey) {
    const openrouter = createOpenAI({
      apiKey: openRouterKey,
      baseURL: OPENROUTER_BASE_URL,
    });
    return { provider: "openrouter", model: openrouter(OPENROUTER_MODEL) };
  }

  const openAiKey = process.env.OPENAI_API_KEY?.trim();
  if (openAiKey) {
    const openai = createOpenAI({ apiKey: openAiKey });
    return { provider: "openai", model: openai(OPENAI_MODEL) };
  }

  throw new Error(
    "set OPENROUTER_API_KEY or OPENAI_API_KEY. " +
      "Note: model strings like openai/gpt-4.1-mini use Vercel AI Gateway and need AI_GATEWAY_API_KEY.",
  );
}

async function main(): Promise<void> {
  const { provider, model } = resolveLanguageModel();
  const { tools, close } = await getWebzTools();
  try {
    console.log("llm provider:", provider);
    printLiveToolSchema(tools);
    console.log("---");
    const result = await generateText({
      model,
      system: SYSTEM_PROMPT,
      prompt: PROMPT,
      tools,
      toolChoice: "auto",
      stopWhen: isStepCount(4),
      onStepFinish: (step) => {
        const calls = step.toolCalls?.map((call) => call.toolName) ?? [];
        if (calls.length > 0) {
          console.log("tool calls:", calls.join(", "));
        }
      },
    });
    console.log("--- final answer ---");
    console.log(result.text);
    if ((result.steps?.length ?? 0) === 1 && !result.toolCalls?.length) {
      console.warn(
        "warning: model finished without calling a tool. try OPENAI_API_KEY or a different OpenRouter model.",
      );
    }
  } finally {
    await close();
  }
}

main().catch((error: unknown) => {
  console.error("agent failed:", error);
  process.exitCode = 1;
});
