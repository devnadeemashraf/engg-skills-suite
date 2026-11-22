import type { Order } from "../domain/order";

export function cancelOrder(order: Order, requesterId: string): Order {
  if (order.ownerId !== requesterId) throw new RangeError("only the owner can cancel an order");
  if (order.status === "cancelled") return order;
  return { ...order, status: "cancelled" };
}
