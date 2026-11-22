// DEFECT D2: pricing <-> place-order import cycle.
import { DEFAULT_CURRENCY } from "./place-order";

export function taxFor(totalCents: number, currency: string = DEFAULT_CURRENCY): number {
  return currency === "EUR" ? Math.round(totalCents * 0.2) : Math.round(totalCents * 0.1);
}
