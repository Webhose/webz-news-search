/**
 * smoke test: installs @webz.io/ai-sdk from npm (not the local src/) and runs a direct search.
 *
 * usage from packages/ai-sdk:
 *   npm run example:npm-smoke
 *
 * reads WEBZ_API_TOKEN from packages/ai-sdk/.env (or from the shell).
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { flattenToolResult, webzNewsSearch } from "@webz.io/ai-sdk";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const ENV_PATH = resolve(PACKAGE_ROOT, ".env");
const QUERY =
  process.env.WEBZ_SMOKE_QUERY ??
  "latest news about artificial intelligence regulation in the EU";

function loadEnvFile() {
  if (!existsSync(ENV_PATH)) {
    return;
  }

  for (const line of readFileSync(ENV_PATH, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const separator = trimmed.indexOf("=");
    if (separator <= 0) {
      continue;
    }
    const key = trimmed.slice(0, separator).trim();
    const value = trimmed.slice(separator + 1).trim();
    if (key && process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

loadEnvFile();

if (!process.env.WEBZ_API_TOKEN?.trim()) {
  console.error(
    "missing WEBZ_API_TOKEN. add it to packages/ai-sdk/.env or export it in the shell.",
  );
  process.exit(1);
}

console.log("package: @webz.io/ai-sdk (from npm registry)");
console.log("query:", QUERY);
console.log("---");

const session = await webzNewsSearch();

try {
  const result = await session.client.callTool({
    name: session.toolName,
    arguments: { query: QUERY, k: 3 },
  });

  const text = flattenToolResult(result);

  if (
    text.includes("validation error") ||
    text.includes("Error executing tool") ||
    !text.includes("Total results")
  ) {
    console.error(text);
    console.error("---");
    console.error("FAILED: unexpected response from news search");
    process.exit(1);
  }

  console.log(text);
  console.log("---");
  console.log("SUCCESS: npm package smoke test passed");
} finally {
  await session.close();
}
