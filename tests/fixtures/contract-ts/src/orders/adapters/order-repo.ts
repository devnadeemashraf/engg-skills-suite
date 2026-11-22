import type { Order } from "../domain/order";
import { placeOrder } from "../app/place-order";

export const seed: Order = placeOrder("o-1", 100);
