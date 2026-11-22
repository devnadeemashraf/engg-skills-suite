import { OrderNotFound, type Order, type OrderStore } from "../domain/order";

/** Returns the order only to its owner. Another user's order is reported as not found, so ids can't be probed. */
export async function getOrderForUser(store: OrderStore, userId: string, orderId: string): Promise<Order> {
  const order = await store.findById(orderId);
  if (!order || order.ownerId !== userId) throw new OrderNotFound(orderId);
  return order;
}
