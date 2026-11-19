#!/usr/bin/env node
import { DEFAULT_HOST, DEFAULT_PORT, HOST_ENV_NAME } from "./consts.js";
import { WebzConfigError } from "./errors.js";
import { listen } from "./server.js";

const host = process.env[HOST_ENV_NAME]?.trim() || DEFAULT_HOST;
const rawPort = process.env.PORT?.trim();
const port = rawPort ? Number(rawPort) : DEFAULT_PORT;

if (!Number.isInteger(port) || port < 0 || port > 65535) {
  console.error("PORT must be an integer from 0 to 65535.");
  process.exit(1);
}

listen({ host, port }).then(
  (server) => {
    const address = server.address();
    const shown = address && typeof address === "object" ? address.port : port;
    console.log(`Webz.io News Search relay listening on http://${host}:${shown}`);
  },
  (error: unknown) => {
    const message = error instanceof WebzConfigError || error instanceof Error ? error.message : String(error);
    console.error(message);
    process.exit(1);
  },
);
