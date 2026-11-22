import type { Order } from "../domain/order";

export function placeOrder(id: string, totalCents: number): Order {
  return { id, totalCents };
}
