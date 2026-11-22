import { PAYMENT_URL } from "../../config";

export async function charge(orderId: string, amountCents: number): Promise<boolean> {
  try {
    // DEFECT D5: no timeout or AbortSignal; a hung payment provider hangs the request forever.
    const res = await fetch(`${PAYMENT_URL}/charges`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ orderId, amountCents }),
    });
    return res.ok;
  } catch {
    // DEFECT D12: the error is swallowed; callers can't tell "declined" from "provider down".
    return false;
  }
}
