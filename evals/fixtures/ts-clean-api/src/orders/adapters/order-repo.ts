import type { Order, OrderStatus, OrderStore } from "../domain/order";

interface OrderRow {
  id: string;
  owner_id: string;
  total_cents: number;
  status: OrderStatus;
}

export interface Db {
  /** Parameterised query: values are sent separately from the SQL text. */
  query(sql: string, params: readonly unknown[]): Promise<OrderRow[]>;
}

function fromRow(row: OrderRow): Order {
  return { id: row.id, ownerId: row.owner_id, totalCents: row.total_cents, status: row.status };
}

export function sqlOrderStore(db: Db): OrderStore {
  return {
    async findById(id) {
      const rows = await db.query("SELECT id, owner_id, total_cents, status FROM orders WHERE id = $1", [id]);
      return rows[0] ? fromRow(rows[0]) : undefined;
    },
    async findByStatus(status) {
      const rows = await db.query(
        "SELECT id, owner_id, total_cents, status FROM orders WHERE status = $1 ORDER BY id LIMIT 100",
        [status],
      );
      return rows.map(fromRow);
    },
  };
}
