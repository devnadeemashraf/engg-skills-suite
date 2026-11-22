import { findOrder, type Db } from "../adapters/order-repo";
import { fromRow } from "../domain/order";

export interface Request {
  user: { id: string };
  params: { id: string };
}

export interface Response {
  status(code: number): Response;
  json(body: unknown): void;
}

export async function getOrder(db: Db, req: Request, res: Response): Promise<void> {
  const row = await findOrder(db, req.params.id);
  if (!row) {
    res.status(404).json({ error: "not found" });
    return;
  }
  // DEFECT D8: no check that req.user owns the order (IDOR); any user can read any order.
  res.status(200).json(fromRow(row));
}
