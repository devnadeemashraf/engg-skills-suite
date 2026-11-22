import type { Order } from "../domain/order";

export interface OrderRow {
  id: string;
  owner_id: string;
  total_cents: number;
  status: "open" | "cancelled";
}

export interface Db {
  query(sql: string): Promise<OrderRow[]>;
}

export async function findOrdersByStatus(db: Db, status: string): Promise<OrderRow[]> {
  // DEFECT D7: SQL built by string concatenation from caller input (injection).
  return db.query("SELECT * FROM orders WHERE status = '" + status + "'");
}

export async function findOrder(db: Db, id: string): Promise<OrderRow | undefined> {
  const rows = await db.query("SELECT * FROM orders WHERE id = '" + id + "'");
  return rows[0];
}

export function toRow(order: Order): OrderRow {
  return { id: order.id, owner_id: order.ownerId, total_cents: order.totalCents, status: order.status };
}
