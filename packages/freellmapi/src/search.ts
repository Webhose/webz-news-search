import {
  API_URL_ENV_NAME,
  CONTENT_CHARS,
  DEFAULT_API_URL,
  DEFAULT_MAX_RESULTS,
  MAX_QUERY_CHARS,
  MAX_QUERY_WORDS,
  MAX_RESULTS,
  NO_KEY_SENTINEL,
  PLATFORM,
  PROVIDER_NAME,
  REQUEST_TIMEOUT_MS,
  TOKEN_ENV_NAME,
  USER_AGENT,
} from "./consts.js";
import { WebzAPIError, WebzConfigError, type KeyValidationResult } from "./errors.js";

export interface TavilySearchRequest {
  query: string;
  max_results?: number;
  topic?: "general" | "news";
  include_answer?: boolean;
}

export interface TavilyHit {
  title: string;
  url: string;
  content: string;
  score?: number;
}

export interface TavilySearchResponse {
  query: string;
  results: TavilyHit[];
}

export interface ClientOptions {
  apiToken?: string;
  apiUrl?: string;
  fetchImpl?: typeof fetch;
}

export function isAnonymousCredential(apiKey: string | null | undefined): boolean {
  const value = apiKey?.trim() ?? "";
  return value === "" || value === NO_KEY_SENTINEL;
}

export function resolveApiToken(apiToken?: string): string {
  const token = (apiToken ?? process.env[TOKEN_ENV_NAME] ?? "").trim();
  if (isAnonymousCredential(token)) {
    throw new WebzConfigError(
      `missing Webz API token. set ${TOKEN_ENV_NAME} or pass the token.`,
    );
  }
  return token;
}

export function resolveApiUrl(apiUrl?: string): string {
  const raw = (apiUrl ?? process.env[API_URL_ENV_NAME] ?? DEFAULT_API_URL).trim();
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new WebzConfigError(httpsUrlMessage(raw));
  }
  if (parsed.protocol !== "https:" || parsed.host.length === 0) {
    throw new WebzConfigError(httpsUrlMessage(raw));
  }
  return parsed.href;
}

function httpsUrlMessage(url: string): string {
  return `The News Search API URL must be an absolute https:// URL, got ${JSON.stringify(url)}.`;
}

export function requestHeaders(apiToken: string): Record<string, string> {
  return {
    Authorization: `Bearer ${apiToken}`,
    "Content-Type": "application/json",
    Accept: "application/json",
    "User-Agent": USER_AGENT,
  };
}

export function normalizeQuery(query: unknown): string {
  if (typeof query !== "string") {
    throw new WebzConfigError("query is required.");
  }
  const text = query.trim();
  if (!text) {
    throw new WebzConfigError("query is required.");
  }
  if (text.length > MAX_QUERY_CHARS) {
    throw new WebzConfigError(
      `query is too long: ${text.length} characters (max ${MAX_QUERY_CHARS}).`,
    );
  }
  const words = text.split(/\s+/).length;
  if (words > MAX_QUERY_WORDS) {
    throw new WebzConfigError(`query is too long: ${words} words (max ${MAX_QUERY_WORDS}).`);
  }
  return text;
}

export function normalizeMaxResults(maxResults: unknown): number {
  if (maxResults === undefined) {
    return DEFAULT_MAX_RESULTS;
  }
  if (typeof maxResults !== "number" || !Number.isInteger(maxResults) || maxResults < 1 || maxResults > MAX_RESULTS) {
    throw new WebzConfigError(`max_results must be an integer from 1 to ${MAX_RESULTS}.`);
  }
  return maxResults;
}

/** Tavily's search body, translated to POST /api/news/context. `days` is not a field on that API. */
export function buildSearchBody(request: TavilySearchRequest): { query: string; k: number } {
  if (request.topic !== undefined && request.topic !== "general" && request.topic !== "news") {
    throw new WebzConfigError("topic must be general or news.");
  }
  if (request.include_answer !== undefined && typeof request.include_answer !== "boolean") {
    throw new WebzConfigError("include_answer must be a boolean.");
  }
  return {
    query: normalizeQuery(request.query),
    k: normalizeMaxResults(request.max_results),
  };
}

function clip(text: string): string {
  return text.length > CONTENT_CHARS ? `${text.slice(0, CONTENT_CHARS)}…` : text;
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return undefined;
  }
  return value as Record<string, unknown>;
}

export function toTavilyResponse(payload: unknown, query: string): TavilySearchResponse {
  const root = asRecord(payload);
  const rows = Array.isArray(root?.results) ? root.results : [];
  const results: TavilyHit[] = [];
  for (const row of rows) {
    const item = asRecord(row);
    if (!item) {
      continue;
    }
    const article = asRecord(item.article);
    const chunk = asRecord(item.chunk);
    const url = typeof article?.url === "string" ? article.url : "";
    if (!url) {
      continue;
    }
    const hit: TavilyHit = {
      title: typeof article?.title === "string" ? article.title : "",
      url,
      content: clip(typeof chunk?.text === "string" ? chunk.text : ""),
    };
    if (typeof item.score === "number" && Number.isFinite(item.score)) {
      hit.score = item.score;
    }
    results.push(hit);
  }
  return { query, results };
}

export function extractErrorDetail(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return "";
  }
  try {
    const payload = JSON.parse(trimmed) as unknown;
    const record = asRecord(payload);
    const detail = record?.detail ?? record?.message ?? record?.error;
    if (typeof detail === "string") {
      return detail.slice(0, 500);
    }
    if (detail !== undefined) {
      return JSON.stringify(detail).slice(0, 500);
    }
  } catch {
    return trimmed.slice(0, 500);
  }
  return trimmed.slice(0, 500);
}

function redact(message: string, token: string): string {
  return token ? message.split(token).join("[redacted]") : message;
}

async function readBody(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

/**
 * Proves a token without running a search.
 *
 * POST {} has no query. A bad token is HTTP 401. A good token is HTTP 422
 * (`query` is required) before any article lookup. That matches
 * SearchOnlyProvider.probe: 401/403 is an invalid key, any other 4xx still
 * proves the key authenticated, and 5xx or a transport failure throws.
 */
export async function validateKey(
  apiKey: string,
  options: ClientOptions = {},
): Promise<KeyValidationResult> {
  if (isAnonymousCredential(apiKey)) {
    return { valid: false, error: `${PROVIDER_NAME} key validation failed: invalid API key` };
  }
  const apiUrl = resolveApiUrl(options.apiUrl);
  const fetchImpl = options.fetchImpl ?? fetch;
  let response: Response;
  try {
    response = await fetchImpl(apiUrl, {
      method: "POST",
      headers: requestHeaders(apiKey),
      body: "{}",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    throw new Error(`${PROVIDER_NAME} key validation inconclusive: ${redact(message, apiKey)}`);
  }
  await readBody(response);
  if (response.ok) {
    return true;
  }
  if (response.status === 401 || response.status === 403) {
    return {
      valid: false,
      error: `${PROVIDER_NAME} key validation failed (HTTP ${response.status}): invalid API key`,
    };
  }
  if (response.status >= 400 && response.status < 500) {
    return true;
  }
  throw new Error(`${PROVIDER_NAME} key validation inconclusive (HTTP ${response.status})`);
}

export async function searchNews(
  request: TavilySearchRequest,
  options: ClientOptions = {},
): Promise<TavilySearchResponse> {
  const apiUrl = resolveApiUrl(options.apiUrl);
  const apiToken = resolveApiToken(options.apiToken);
  const body = buildSearchBody(request);
  const fetchImpl = options.fetchImpl ?? fetch;
  let response: Response;
  try {
    response = await fetchImpl(apiUrl, {
      method: "POST",
      headers: requestHeaders(apiToken),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    throw new WebzAPIError(`could not reach the News Search API: ${redact(message, apiToken)}`, 0);
  }
  const text = await readBody(response);
  if (!response.ok) {
    const detail = redact(extractErrorDetail(text), apiToken);
    const retryAfter = response.headers.get("retry-after") ?? undefined;
    throw new WebzAPIError(
      detail || `News Search API returned HTTP ${response.status}`,
      response.status,
      retryAfter,
    );
  }
  let payload: unknown;
  try {
    payload = JSON.parse(text) as unknown;
  } catch {
    throw new WebzAPIError("response was not valid JSON", response.status);
  }
  return toTavilyResponse(payload, body.query);
}

/**
 * Search-only provider. FreeLLMAPI's SearchOnlyProvider is not a published
 * package (`@freellmapi/server` is private), so this class copies that
 * contract: chat is refused, and validateKey does not run a search.
 * FreeLLMAPI loads the HTTP relay, not this class, through a custom search
 * endpoint that speaks Tavily's POST /search shape.
 */
export class WebzSearchProvider {
  readonly platform = PLATFORM;
  readonly name = PROVIDER_NAME;
  readonly supportsChat = false;

  constructor(private readonly options: ClientOptions = {}) {}

  validateKey(apiKey: string): Promise<KeyValidationResult> {
    return validateKey(apiKey, this.options);
  }

  search(request: TavilySearchRequest, apiToken?: string): Promise<TavilySearchResponse> {
    return searchNews(request, { ...this.options, apiToken: apiToken ?? this.options.apiToken });
  }

  chatCompletion(): never {
    throw Object.assign(
      new Error(`${this.name} is a search provider: its key serves POST /search, not chat completions`),
      { status: 422 },
    );
  }
}
