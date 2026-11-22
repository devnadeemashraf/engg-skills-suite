import type { Invoice } from "../domain/invoice";
import { placeOrder } from "../../orders/index";

export function bill(orderId: string): Invoice {
  const order = placeOrder(orderId, 100);
  return { orderId: order.id, amountCents: order.totalCents };
}
