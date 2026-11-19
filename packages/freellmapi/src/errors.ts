export class WebzConfigError extends Error {
  readonly status: number;

  constructor(message: string, status = 400) {
    super(message);
    this.name = "WebzConfigError";
    this.status = status;
  }
}

export class WebzAPIError extends Error {
  readonly status: number;
  readonly retryAfter: string | undefined;

  constructor(message: string, status: number, retryAfter?: string) {
    super(message);
    this.name = "WebzAPIError";
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

/** Same verdict SearchOnlyProvider.probe returns: true, or a hard invalid key. */
export type KeyValidationResult = true | { valid: false; error: string };
