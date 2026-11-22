import { DEFAULT_CURRENCY, percentOf } from "../domain/money";

export function taxFor(totalCents: number, currency: string = DEFAULT_CURRENCY): number {
  return percentOf(totalCents, currency === "EUR" ? 20 : 10);
}
