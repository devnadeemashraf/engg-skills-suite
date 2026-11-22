import { strict as assert } from "node:assert";
import { test } from "node:test";
import { placeOrder } from "./place-order";

const id = () => "o-1";

test("applies quantity discount, coupon and tax in integer cents", () => {
  const order = placeOrder(
    { ownerId: "u-1", email: "a@b.co", items: [{ sku: "x", qty: 11, unitPriceCents: 1000 }], coupon: "TENOFF" },
    id,
  );
  // 11 x 1000 = 11000, -5% = 10450, -1000 = 9450, +10% tax = 10395
  assert.equal(order.totalCents, 10395);
});

test("rejects an invalid email", () => {
  assert.throws(() => placeOrder({ ownerId: "u-1", email: "nope", items: [] }, id), RangeError);
});

test("rejects a non-integer quantity", () => {
  assert.throws(
    () => placeOrder({ ownerId: "u-1", email: "a@b.co", items: [{ sku: "x", qty: 1.5, unitPriceCents: 1 }] }, id),
    RangeError,
  );
});
