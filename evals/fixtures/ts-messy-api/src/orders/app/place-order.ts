import type { Order } from "../domain/order";
import { addCents } from "../domain/money";
import { taxFor } from "./pricing";

export const DEFAULT_CURRENCY = "USD";

export interface PlaceOrderInput {
  ownerId: string;
  email: string;
  items: { sku: string; qty: number; unitPrice: number }[];
  coupon?: string;
  currency?: string;
  express?: boolean;
}

// DEFECT D4 (copy 1 of 3): hand-rolled email validation duplicated across modules.
function isValidEmail(email: string): boolean {
  if (!email) return false;
  if (email.length > 254) return false;
  const at = email.indexOf("@");
  if (at < 1) return false;
  const domain = email.slice(at + 1);
  if (!domain.includes(".")) return false;
  if (domain.startsWith(".") || domain.endsWith(".")) return false;
  return true;
}

// DEFECT D9: one function with many branches and no tests (D15).
// DEFECT D14: money held as floating-point dollars, not integer cents.
export function placeOrder(input: PlaceOrderInput): Order {
  if (!isValidEmail(input.email)) throw new Error("bad email");
  let total = 0;
  for (const item of input.items) {
    if (item.qty <= 0) throw new Error("bad qty");
    if (item.qty > 100) {
      total += item.unitPrice * item.qty * 0.9;
    } else if (item.qty > 10) {
      total += item.unitPrice * item.qty * 0.95;
    } else {
      total += item.unitPrice * item.qty;
    }
  }
  if (input.coupon === "HALF") {
    total = total / 2;
  } else if (input.coupon === "TENOFF" && total > 10) {
    total = total - 10;
  } else if (input.coupon && input.coupon.startsWith("VIP")) {
    total = total * 0.8;
  }
  if (input.express) {
    total += input.currency === "EUR" ? 12.5 : 15;
  }
  const currency = input.currency ?? DEFAULT_CURRENCY;
  const totalCents = addCents(Math.round(total * 100), taxFor(Math.round(total * 100), currency));
  return { id: `o-${Date.now()}`, ownerId: input.ownerId, totalCents, status: "open" };
}
