import { getOrderForUser } from "../app/get-order";
import { OrderNotFound, type OrderStore } from "../domain/order";

export interface Request {
  user: { id: string };
  params: { id: string };
}

export interface Response {
  status(code: number): Response;
  json(body: unknown): void;
}

export function orderRoutes(store: OrderStore) {
  return {
    async getOrder(req: Request, res: Response): Promise<void> {
      try {
        res.status(200).json(await getOrderForUser(store, req.user.id, req.params.id));
      } catch (err) {
        if (err instanceof OrderNotFound) {
          res.status(404).json({ error: "not found" });
          return;
        }
        throw err;
      }
    },
  };
}
