// DEFECT D11: a one-off script inside src/ that belongs to no layer.
import { toRow } from "../orders/adapters/order-repo";

export function migrateAll(orders: { id: string; ownerId: string; totalCents: number }[]): unknown[] {
  return orders.map((o) => toRow({ ...o, status: "open" }));
}
