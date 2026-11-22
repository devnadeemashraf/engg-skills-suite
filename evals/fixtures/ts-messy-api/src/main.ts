import { placeOrder } from "./orders";
import { getOrder } from "./orders/http/routes";
import { findOrdersByStatus } from "./orders/adapters/order-repo";
import { charge } from "./orders/adapters/payment-client";
import { register } from "./users/app/register";
import { formatCurrency } from "./shared";

export const app = { placeOrder, getOrder, findOrdersByStatus, charge, register, formatCurrency };
