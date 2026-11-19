import { describe, expect, it } from "vitest";

import { TOKEN_ENV_NAME, WebzSearchProvider } from "../src/index.js";

const hasToken = Boolean(process.env[TOKEN_ENV_NAME]?.trim());

describe.skipIf(!hasToken)("live News Search API", () => {
  const provider = new WebzSearchProvider();

  it("accepts the configured token without running a search", async () => {
    await expect(provider.validateKey(process.env[TOKEN_ENV_NAME] ?? "")).resolves.toBe(true);
  });

  it("returns one article for a Tavily-shaped query", async () => {
    const response = await provider.search({
      query: "AI regulation Europe",
      max_results: 1,
      topic: "news",
    });
    expect(response.results.length).toBeGreaterThan(0);
    expect(response.results[0]?.url.startsWith("https://")).toBe(true);
    expect(response.results[0]?.title.length).toBeGreaterThan(0);
    expect("answer" in response).toBe(false);
  });
});
