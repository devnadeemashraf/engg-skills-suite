import { loadConfig } from "./config";
import { cancelOrder, placeOrder } from "./orders";
import { sqlOrderStore, type Db } from "./orders/adapters/order-repo";
import { paymentClient } from "./orders/adapters/payment-client";
import { orderRoutes } from "./orders/http/routes";
import { register } from "./users/app/register";
import { formatCurrency } from "./shared";

export function compose(db: Db) {
  const config = loadConfig();
  const store = sqlOrderStore(db);
  return {
    routes: orderRoutes(store),
    payments: paymentClient({ baseUrl: config.paymentUrl, timeoutMs: config.paymentTimeoutMs }),
    placeOrder,
    cancelOrder,
    register,
    formatCurrency,
  };
}
