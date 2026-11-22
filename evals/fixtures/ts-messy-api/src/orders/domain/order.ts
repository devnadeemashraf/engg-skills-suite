// DEFECT D1: the domain imports an adapter (layer violation).
import { OrderRow } from "../adapters/order-repo";

export interface Order {
  id: string;
  ownerId: string;
  totalCents: number;
  status: "open" | "cancelled";
}

export function fromRow(row: OrderRow): Order {
  return { id: row.id, ownerId: row.owner_id, totalCents: row.total_cents, status: row.status };
}
