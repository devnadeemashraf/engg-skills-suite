export interface Config {
  paymentUrl: string;
  paymentTimeoutMs: number;
  paymentApiSecret: string;
}

/** Reads configuration from the environment and fails fast at startup if anything is missing. */
export function loadConfig(env: Record<string, string | undefined> = process.env): Config {
  const missing = ["PAYMENT_URL", "PAYMENT_API_SECRET"].filter((k) => !env[k]);
  if (missing.length) throw new Error(`missing required environment variables: ${missing.join(", ")}`);
  const timeout = Number(env.PAYMENT_TIMEOUT_MS ?? "5000");
  if (!Number.isInteger(timeout) || timeout <= 0) throw new Error("PAYMENT_TIMEOUT_MS must be a positive integer");
  return { paymentUrl: env.PAYMENT_URL!, paymentTimeoutMs: timeout, paymentApiSecret: env.PAYMENT_API_SECRET! };
}
