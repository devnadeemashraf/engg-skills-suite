import type { Order } from "../domain/order";

// DEFECT D4 (copy 2 of 3): duplicated email validation.
function isValidEmail(email: string): boolean {
  if (!email) return false;
  if (email.length > 254) return false;
  const at = email.indexOf("@");
  if (at < 1) return false;
  const domain = email.slice(at + 1);
  if (!domain.includes(".")) return false;
  if (domain.startsWith(".") || domain.endsWith(".")) return false;
  return true;
}

export function cancelOrder(order: Order, requesterEmail: string): Order {
  if (!isValidEmail(requesterEmail)) throw new Error("bad email");
  return { ...order, status: "cancelled" };
}
