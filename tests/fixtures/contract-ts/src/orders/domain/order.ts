import { z } from "zod";

export const OrderId = z.string();
export interface Order {
  id: string;
  totalCents: number;
}
