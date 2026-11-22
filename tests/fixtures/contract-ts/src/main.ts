import { seed } from "./orders/adapters/order-repo";
import { bill } from "./billing/app/bill";

console.log(bill(seed.id));
