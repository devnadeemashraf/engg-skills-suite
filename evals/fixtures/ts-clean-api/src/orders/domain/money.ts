export const DEFAULT_CURRENCY = "USD";

export function addCents(a: number, b: number): number {
  if (!Number.isInteger(a) || !Number.isInteger(b)) {
    throw new RangeError("cents must be integers");
  }
  return a + b;
}

export function percentOf(cents: number, percent: number): number {
  if (!Number.isInteger(cents)) throw new RangeError("cents must be an integer");
  return Math.round((cents * percent) / 100);
}
