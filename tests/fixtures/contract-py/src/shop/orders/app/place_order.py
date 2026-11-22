from shop.orders.domain.order import Order


def place_order(order_id: str, total_cents: int) -> Order:
    return Order(order_id, total_cents)
