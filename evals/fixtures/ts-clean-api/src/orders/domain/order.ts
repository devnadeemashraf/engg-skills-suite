export type OrderStatus = "open" | "cancelled";

export interface Order {
  readonly id: string;
  readonly ownerId: string;
  readonly totalCents: number;
  readonly status: OrderStatus;
}

export interface OrderStore {
  findById(id: string): Promise<Order | undefined>;
  findByStatus(status: OrderStatus): Promise<Order[]>;
}

export class OrderNotFound extends Error {
  constructor(readonly orderId: string) {
    super(`order ${orderId} not found`);
  }
}
