import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  API_URL_ENV_NAME,
  DEFAULT_API_URL,
  TOKEN_ENV_NAME,
  WebzAPIError,
  WebzConfigError,
  WebzSearchProvider,
  buildSearchBody,
  searchNews,
  validateKey,
} from "../src/index.js";

const ORIGINAL_ENV = {
  token: process.env[TOKEN_ENV_NAME],
  url: process.env[API_URL_ENV_NAME],
};

function jsonResponse(status: number, body: unknown, headers?: Record<string, string>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...headers },
  });
}

const ARTICLE = {
  score: 8.2,
  article: {
    url: "https://example.com/story",
    title: "Example headline",
  },
  chunk: { text: "Relevant excerpt." },
};

beforeEach(() => {
  delete process.env[TOKEN_ENV_NAME];
  delete process.env[API_URL_ENV_NAME];
});

afterEach(() => {
  if (ORIGINAL_ENV.token === undefined) {
    delete process.env[TOKEN_ENV_NAME];
  } else {
    process.env[TOKEN_ENV_NAME] = ORIGINAL_ENV.token;
  }
  if (ORIGINAL_ENV.url === undefined) {
    delete process.env[API_URL_ENV_NAME];
  } else {
    process.env[API_URL_ENV_NAME] = ORIGINAL_ENV.url;
  }
});

describe("buildSearchBody", () => {
  it("sends query and k, and does not send days or topic", () => {
    expect(buildSearchBody({ query: "  EU AI regulation  ", max_results: 3, topic: "news" })).toEqual({
      query: "EU AI regulation",
      k: 3,
    });
    expect(Object.keys(buildSearchBody({ query: "ports", include_answer: true }))).toEqual(["query", "k"]);
  });

  it("defaults max_results to 5 and rejects values outside 1..20", () => {
    expect(buildSearchBody({ query: "ports" }).k).toBe(5);
    expect(() => buildSearchBody({ query: "ports", max_results: 0 })).toThrow(WebzConfigError);
    expect(() => buildSearchBody({ query: "ports", max_results: 21 })).toThrow(WebzConfigError);
    expect(() => buildSearchBody({ query: "ports", max_results: 1.5 })).toThrow(WebzConfigError);
  });

  it("rejects an empty, overlong, or non-string query", () => {
    expect(() => buildSearchBody({ query: "   " })).toThrow(/query is required/);
    expect(() => buildSearchBody({ query: "a".repeat(751) })).toThrow(/characters/);
    expect(() => buildSearchBody({ query: Array.from({ length: 101 }, () => "word").join(" ") })).toThrow(/words/);
    expect(() => buildSearchBody({ query: 12 as unknown as string })).toThrow(WebzConfigError);
  });

  it("rejects a topic outside general and news", () => {
    expect(() => buildSearchBody({ query: "ports", topic: "images" as "news" })).toThrow(/topic/);
  });
});

describe("validateKey", () => {
  it("rejects a non-https API URL before fetch, so the token is not sent", async () => {
    const fetchImpl = vi.fn();
    await expect(
      validateKey("secret-token", { apiUrl: "http://api.webz.io/api/news/context", fetchImpl }),
    ).rejects.toThrow(/https:\/\//);
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("treats an empty body 422 as a valid key and does not send a query", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(422, { detail: [{ msg: "Field required" }] }));
    await expect(validateKey("secret-token", { fetchImpl })).resolves.toBe(true);
    expect(fetchImpl).toHaveBeenCalledOnce();
    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(DEFAULT_API_URL);
    expect(init.method).toBe("POST");
    expect(init.body).toBe("{}");
    expect(new Headers(init.headers).get("authorization")).toBe("Bearer secret-token");
  });

  it("returns invalid on 401 and 403", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(401, { detail: "Unknown API token" }));
    await expect(validateKey("bad", { fetchImpl })).resolves.toEqual({
      valid: false,
      error: expect.stringContaining("HTTP 401"),
    });
    fetchImpl.mockResolvedValue(jsonResponse(403, { detail: "blocked" }));
    await expect(validateKey("bad", { fetchImpl })).resolves.toEqual({
      valid: false,
      error: expect.stringContaining("HTTP 403"),
    });
  });

  it("throws when the probe is inconclusive", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(503, { detail: "down" }));
    await expect(validateKey("secret-token", { fetchImpl })).rejects.toThrow(/inconclusive \(HTTP 503\)/);
    fetchImpl.mockRejectedValue(new Error("socket hang up"));
    await expect(validateKey("secret-token", { fetchImpl })).rejects.toThrow(/inconclusive: socket hang up/);
  });

  it("rejects the no-key sentinel without a network call", async () => {
    const fetchImpl = vi.fn();
    await expect(validateKey("no-key", { fetchImpl })).resolves.toMatchObject({ valid: false });
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});

describe("searchNews", () => {
  it("maps articles to Tavily hits and clips long excerpts", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        results: [
          ARTICLE,
          { score: Number.NaN, article: { url: "https://example.com/second", title: "Second" }, chunk: { text: "x".repeat(1600) } },
          { article: { title: "no url" }, chunk: { text: "skip" } },
        ],
      }),
    );
    const response = await searchNews(
      { query: "EU AI regulation", max_results: 2, topic: "general", include_answer: true },
      { apiToken: "secret-token", fetchImpl },
    );
    expect("answer" in response).toBe(false);
    expect(response.results).toHaveLength(2);
    expect(response.results[0]).toEqual({
      title: "Example headline",
      url: "https://example.com/story",
      content: "Relevant excerpt.",
      score: 8.2,
    });
    expect(response.results[1]?.content.endsWith("…")).toBe(true);
    expect(response.results[1]?.content.length).toBe(1501);
    expect(response.results[1]?.score).toBeUndefined();
    const body = JSON.parse(String((fetchImpl.mock.calls[0]?.[1] as RequestInit).body));
    expect(body).toEqual({ query: "EU AI regulation", k: 2 });
  });

  it("maps upstream auth and credit failures and redacts the token", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(401, { detail: "bad secret-token" }));
    await expect(searchNews({ query: "ports" }, { apiToken: "secret-token", fetchImpl })).rejects.toMatchObject({
      status: 401,
      message: "bad [redacted]",
    });
    fetchImpl.mockResolvedValue(
      jsonResponse(402, { detail: "insufficient credits" }, { "retry-after": "30" }),
    );
    const error = await searchNews({ query: "ports" }, { apiToken: "secret-token", fetchImpl }).catch((err: unknown) => err);
    expect(error).toBeInstanceOf(WebzAPIError);
    expect(error).toMatchObject({ status: 402, retryAfter: "30" });
  });

  it("does not call fetch when the token or URL is unusable", async () => {
    const fetchImpl = vi.fn();
    await expect(searchNews({ query: "ports" }, { fetchImpl })).rejects.toThrow(/missing Webz API token/);
    await expect(
      searchNews({ query: "ports" }, { apiToken: "secret-token", apiUrl: "http://example.test/search", fetchImpl }),
    ).rejects.toThrow(WebzConfigError);
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});

describe("WebzSearchProvider", () => {
  it("refuses chat and stays search-only", () => {
    const provider = new WebzSearchProvider();
    expect(provider.supportsChat).toBe(false);
    expect(provider.platform).toBe("webz");
    expect(() => provider.chatCompletion()).toThrow(/POST \/search/);
    try {
      provider.chatCompletion();
    } catch (error) {
      expect(error).toMatchObject({ status: 422 });
    }
  });
});
