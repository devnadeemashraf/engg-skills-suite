import type { Order } from "../domain/order";
import { addCents, DEFAULT_CURRENCY, percentOf } from "../domain/money";
import { applyCoupon, quantityDiscountPercent } from "../domain/discounts";
import { isValidEmail } from "../../shared";
import { taxFor } from "./pricing";

export interface PlaceOrderInput {
  ownerId: string;
  email: string;
  items: { sku: string; qty: number; unitPriceCents: number }[];
  coupon?: string;
  currency?: string;
}

export function placeOrder(input: PlaceOrderInput, newId: () => string): Order {
  if (!isValidEmail(input.email)) throw new RangeError("invalid email");
  let subtotal = 0;
  for (const item of input.items) {
    if (!Number.isInteger(item.qty) || item.qty <= 0) throw new RangeError("invalid quantity");
    const line = item.unitPriceCents * item.qty;
    subtotal = addCents(subtotal, line - percentOf(line, quantityDiscountPercent(item.qty)));
  }
  const discounted = applyCoupon(subtotal, input.coupon);
  const totalCents = addCents(discounted, taxFor(discounted, input.currency ?? DEFAULT_CURRENCY));
  return { id: newId(), ownerId: input.ownerId, totalCents, status: "open" };
}
