import { isValidEmail, normaliseName } from "../../shared";

export interface User {
  id: string;
  email: string;
  name: string;
}

export function register(id: string, email: string, name: string): User {
  if (!isValidEmail(email)) throw new RangeError("invalid email");
  return { id, email, name: normaliseName(name) };
}
