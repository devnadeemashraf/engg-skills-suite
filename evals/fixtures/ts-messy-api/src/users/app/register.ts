// DEFECT D10: reaches into another module's internals instead of its public entry.
import type { Order } from "../../orders/domain/order";
import { normaliseName } from "../../shared";

export interface User {
  id: string;
  email: string;
  name: string;
  firstOrder?: Order;
}

// DEFECT D4 (copy 3 of 3): duplicated email validation.
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

export function register(id: string, email: string, name: string): User {
  if (!isValidEmail(email)) throw new Error("bad email");
  return { id, email, name: normaliseName(name) };
}
