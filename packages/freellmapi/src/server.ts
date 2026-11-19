import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";

import { DEFAULT_HOST, DEFAULT_PORT, HOST_ENV_NAME, MAX_BODY_BYTES } from "./consts.js";
import { WebzAPIError, WebzConfigError, type KeyValidationResult } from "./errors.js";
import {
  isAnonymousCredential,
  resolveApiToken,
  searchNews,
  validateKey,
  type ClientOptions,
  type TavilySearchRequest,
} from "./search.js";

export interface RelayOptions extends ClientOptions {
  apiToken?: string;
}

function writeJson(res: ServerResponse, status: number, payload: unknown, retryAfter?: string): void {
  const body = JSON.stringify(payload);
  const headers: Record<string, string | number> = {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  };
  if (retryAfter) {
    headers["Retry-After"] = retryAfter;
  }
  res.writeHead(status, headers);
  res.end(body);
}

function bearerToken(header: string | undefined): string | undefined {
  if (!header) {
    return undefined;
  }
  const match = /^Bearer\s+(\S+)\s*$/i.exec(header.trim());
  return match?.[1];
}

function tokenForRequest(req: IncomingMessage, fallback: string | undefined): string {
  const presented = bearerToken(req.headers.authorization);
  if (!isAnonymousCredential(presented)) {
    return presented as string;
  }
  return resolveApiToken(fallback);
}

function readBody(req: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const declared = Number(req.headers["content-length"] ?? "0");
    if (Number.isFinite(declared) && declared > MAX_BODY_BYTES) {
      reject(new WebzConfigError("request body is too large.", 413));
      req.resume();
      return;
    }
    const chunks: Buffer[] = [];
    let size = 0;
    req.on("data", (chunk: Buffer) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new WebzConfigError("request body is too large.", 413));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function relayStatus(error: unknown): number {
  if (error instanceof WebzConfigError) {
    return error.status;
  }
  if (error instanceof WebzAPIError) {
    if (error.status === 401 || error.status === 403) {
      return 401;
    }
    if (error.status === 402 || error.status === 429) {
      return error.status;
    }
    if (error.status === 400 || error.status === 422) {
      return 400;
    }
    return 502;
  }
  return 500;
}

function errorPayload(error: unknown): { detail: string } {
  if (error instanceof Error && error.message) {
    return { detail: error.message };
  }
  return { detail: "request failed" };
}

async function handleUsage(req: IncomingMessage, res: ServerResponse, options: RelayOptions): Promise<void> {
  let token: string;
  try {
    token = tokenForRequest(req, options.apiToken);
  } catch (error) {
    writeJson(res, 401, { valid: false, error: error instanceof Error ? error.message : "missing Webz API token" });
    return;
  }
  try {
    const verdict: KeyValidationResult = await validateKey(token, options);
    if (verdict === true) {
      writeJson(res, 200, { valid: true });
      return;
    }
    writeJson(res, 401, verdict);
  } catch (error) {
    const message = error instanceof Error ? error.message : "key validation inconclusive";
    writeJson(res, 503, { detail: message });
  }
}

async function handleSearch(req: IncomingMessage, res: ServerResponse, options: RelayOptions): Promise<void> {
  const token = tokenForRequest(req, options.apiToken);
  const raw = await readBody(req);
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw || "null") as unknown;
  } catch {
    throw new WebzConfigError("request body must be JSON.");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new WebzConfigError("request body must be a JSON object.");
  }
  const record = parsed as Record<string, unknown>;
  const request: TavilySearchRequest = {
    query: record.query as string,
  };
  if ("max_results" in record) {
    request.max_results = record.max_results as number;
  }
  if ("topic" in record) {
    request.topic = record.topic as TavilySearchRequest["topic"];
  }
  if ("include_answer" in record) {
    request.include_answer = record.include_answer as boolean;
  }
  const result = await searchNews(request, { ...options, apiToken: token });
  writeJson(res, 200, result);
}

async function handle(req: IncomingMessage, res: ServerResponse, options: RelayOptions): Promise<void> {
  const path = new URL(req.url ?? "/", "http://127.0.0.1").pathname;
  if (req.method === "GET" && path === "/usage") {
    await handleUsage(req, res, options);
    return;
  }
  if (req.method === "POST" && path === "/search") {
    await handleSearch(req, res, options);
    return;
  }
  writeJson(res, 404, { detail: "not found" });
}

export function createRelay(options: RelayOptions = {}): Server {
  return createServer((req, res) => {
    handle(req, res, options).catch((error: unknown) => {
      req.resume();
      if (res.headersSent) {
        res.destroy();
        return;
      }
      const status = relayStatus(error);
      const retryAfter = error instanceof WebzAPIError ? error.retryAfter : undefined;
      writeJson(res, status, errorPayload(error), retryAfter);
    });
  });
}

export function listen(options: RelayOptions & { host?: string; port?: number } = {}): Promise<Server> {
  const host = options.host ?? (process.env[HOST_ENV_NAME]?.trim() || DEFAULT_HOST);
  const port = options.port ?? portFromEnv();
  const server = createRelay(options);
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, host, () => {
      server.off("error", reject);
      resolve(server);
    });
  });
}

function portFromEnv(): number {
  const raw = process.env.PORT?.trim();
  if (!raw) {
    return DEFAULT_PORT;
  }
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new WebzConfigError("PORT must be an integer from 0 to 65535.");
  }
  return port;
}
