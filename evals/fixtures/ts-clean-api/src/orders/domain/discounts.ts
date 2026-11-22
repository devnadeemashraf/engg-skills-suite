import { percentOf } from "./money";

export function quantityDiscountPercent(qty: number): number {
  if (qty > 100) return 10;
  if (qty > 10) return 5;
  return 0;
}

export function applyCoupon(totalCents: number, coupon: string | undefined): number {
  if (coupon === "HALF") return totalCents - percentOf(totalCents, 50);
  if (coupon === "TENOFF") return Math.max(0, totalCents - 1000);
  return totalCents;
}
