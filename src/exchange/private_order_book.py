from src.models.order import PublicOrder


class PrivateOrderBook:
    def __init__(self):
        self._orders: dict[str, PublicOrder] = {}

    def add(self, order: PublicOrder) -> None:
        if not order.proof_valid:
            raise ValueError(
                "Cannot add an order with an invalid proof"
            )

        if order.order_id in self._orders:
            raise ValueError(
                f"Order already exists: {order.order_id}"
            )

        self._orders[order.order_id] = order

    def get(self, order_id: str) -> PublicOrder:
        try:
            return self._orders[order_id]
        except KeyError as error:
            raise KeyError(
                f"Order not found: {order_id}"
            ) from error

    def remove(self, order_id: str) -> PublicOrder:
        try:
            return self._orders.pop(order_id)
        except KeyError as error:
            raise KeyError(
                f"Order not found: {order_id}"
            ) from error

    def all(self) -> list[PublicOrder]:
        return list(self._orders.values())

    def get_by_side(self, side: str) -> list[PublicOrder]:
        return [
            order
            for order in self._orders.values()
            if order.side == side
        ]

    def get_by_asset(self, asset: str) -> list[PublicOrder]:
        return [
            order
            for order in self._orders.values()
            if order.asset == asset
        ]

    def __len__(self) -> int:
        return len(self._orders)