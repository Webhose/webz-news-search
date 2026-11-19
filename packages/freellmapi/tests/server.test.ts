import type { AddressInfo } from "node:net";

import { afterEach, describe, expect, it, vi } from "vitest";

import { TOKEN_ENV_NAME, createRelay, type RelayOptions } from "../src/index.js";

function jsonResponse(status: number, body: unknown, headers?: Record<string, string>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

async function withRelay(
  options: RelayOptions,
  run: (baseUrl: string) => Promise<void>,
): Promise<void> {
  const server = createRelay(options);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address() as AddressInfo;
  try {
    await run(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
  }
}

describe("relay HTTP", () => {
  const originalToken = process.env[TOKEN_ENV_NAME];

  afterEach(() => {
    if (originalToken === undefined) {
      delete process.env[TOKEN_ENV_NAME];
    } else {
      process.env[TOKEN_ENV_NAME] = originalToken;
    }
    vi.restoreAllMocks();
  });

  it("serves POST /search in Tavily's shape using the bearer token", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        results: [
          {
            score: 6,
            article: { title: "Headline", url: "https://example.com/a" },
            chunk: { text: "Excerpt" },
          },
        ],
      }),
    );
    await withRelay({ fetchImpl }, async (baseUrl) => {
      const response = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: { Authorization: "Bearer stored-token", "Content-Type": "application/json" },
        body: JSON.stringify({ query: "EU AI regulation", max_results: 4, topic: "news", include_answer: false }),
      });
      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual({
        query: "EU AI regulation",
        results: [{ title: "Headline", url: "https://example.com/a", content: "Excerpt", score: 6 }],
      });
    });
    const init = fetchImpl.mock.calls[0]?.[1] as RequestInit;
    expect(new Headers(init.headers).get("authorization")).toBe("Bearer stored-token");
    expect(JSON.parse(String(init.body))).toEqual({ query: "EU AI regulation", k: 4 });
  });

  it("uses WEBZ_API_TOKEN when the caller sends the keyless sentinel", async () => {
    process.env[TOKEN_ENV_NAME] = "env-token";
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, { results: [] }));
    await withRelay({ fetchImpl }, async (baseUrl) => {
      const response = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: { Authorization: "Bearer no-key", "Content-Type": "application/json" },
        body: JSON.stringify({ query: "ports" }),
      });
      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual({ query: "ports", results: [] });
    });
    expect(new Headers((fetchImpl.mock.calls[0]?.[1] as RequestInit).headers).get("authorization")).toBe(
      "Bearer env-token",
    );
  });

  it("maps an upstream 401 to 401 and an upstream 429 to 429", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Unknown API token" }))
      .mockResolvedValueOnce(jsonResponse(429, { detail: "slow down" }, { "retry-after": "12" }));
    await withRelay({ fetchImpl, apiToken: "stored-token" }, async (baseUrl) => {
      const denied = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "ports" }),
      });
      expect(denied.status).toBe(401);
      const limited = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "ports" }),
      });
      expect(limited.status).toBe(429);
      expect(limited.headers.get("retry-after")).toBe("12");
    });
  });

  it("checks the key on GET /usage without sending a query", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(422, { detail: [{ msg: "Field required" }] }));
    await withRelay({ fetchImpl, apiToken: "stored-token" }, async (baseUrl) => {
      const response = await fetch(`${baseUrl}/usage`);
      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual({ valid: true });
    });
    expect((fetchImpl.mock.calls[0]?.[1] as RequestInit).body).toBe("{}");
  });

  it("returns 401 from GET /usage for a rejected token and 503 when the probe is inconclusive", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Unknown API token" }))
      .mockRejectedValueOnce(new Error("network down"));
    await withRelay({ fetchImpl, apiToken: "stored-token" }, async (baseUrl) => {
      const invalid = await fetch(`${baseUrl}/usage`);
      expect(invalid.status).toBe(401);
      const inconclusive = await fetch(`${baseUrl}/usage`);
      expect(inconclusive.status).toBe(503);
      await expect(inconclusive.json()).resolves.toMatchObject({ detail: expect.stringContaining("inconclusive") });
    });
  });

  it("rejects a non-https News Search URL before fetch", async () => {
    const fetchImpl = vi.fn();
    await withRelay({ fetchImpl, apiUrl: "http://api.webz.io/api/news/context", apiToken: "stored-token" }, async (baseUrl) => {
      const response = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "ports" }),
      });
      expect(response.status).toBe(400);
      await expect(response.json()).resolves.toMatchObject({ detail: expect.stringContaining("https://") });
    });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("returns 404 for unknown routes", async () => {
    await withRelay({}, async (baseUrl) => {
      const response = await fetch(`${baseUrl}/v1/chat/completions`, { method: "POST" });
      expect(response.status).toBe(404);
    });
  });
});
