from shop.orders.app.place_order import place_order
from shop.orders.domain.order import Order

SEED: Order = place_order("o-1", 100)
