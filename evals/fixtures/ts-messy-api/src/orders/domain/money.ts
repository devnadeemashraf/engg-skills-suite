export function addCents(a: number, b: number): number {
  if (!Number.isInteger(a) || !Number.isInteger(b)) {
    throw new RangeError("cents must be integers");
  }
  return a + b;
}
