export class PaymentDeclined extends Error {}

export class PaymentUnavailable extends Error {
  constructor(message: string, readonly cause?: unknown) {
    super(message);
  }
}

export interface PaymentClientOptions {
  baseUrl: string;
  timeoutMs: number;
}

export function paymentClient(options: PaymentClientOptions) {
  return {
    async charge(orderId: string, amountCents: number): Promise<void> {
      let res: Response;
      try {
        res = await fetch(`${options.baseUrl}/charges`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ orderId, amountCents }),
          signal: AbortSignal.timeout(options.timeoutMs),
        });
      } catch (err) {
        throw new PaymentUnavailable("payment provider unreachable or timed out", err);
      }
      if (res.status === 402) throw new PaymentDeclined(`charge for ${orderId} declined`);
      if (!res.ok) throw new PaymentUnavailable(`payment provider returned ${res.status}`);
    },
  };
}
