from dataclasses import dataclass, field
from time import time
from uuid import uuid4

from src.models.match import MatchResult


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    buy_order_id: str
    sell_order_id: str
    status: str
    executed_quantity: int
    buyer_remaining_quantity: int
    seller_remaining_quantity: int
    buyer_status: str
    seller_status: str
    timestamp: float = field(default_factory=time)


class SettlementEngine:
    def __init__(self):
        self._records: list[SettlementRecord] = []

    def settle(
        self,
        match: MatchResult,
        buy_quantity: int,
        sell_quantity: int,
    ) -> SettlementRecord:
        if not match.valid:
            raise ValueError("Cannot settle an invalid match")

        if buy_quantity <= 0 or sell_quantity <= 0:
            raise ValueError("Order quantities must be positive")

        executed_quantity = min(
            buy_quantity,
            sell_quantity,
        )

        buyer_remaining_quantity = (
            buy_quantity - executed_quantity
        )

        seller_remaining_quantity = (
            sell_quantity - executed_quantity
        )

        buyer_status = (
            "FILLED"
            if buyer_remaining_quantity == 0
            else "PARTIALLY_FILLED"
        )

        seller_status = (
            "FILLED"
            if seller_remaining_quantity == 0
            else "PARTIALLY_FILLED"
        )

        status = (
            "SETTLED"
            if (
                buyer_remaining_quantity == 0
                and seller_remaining_quantity == 0
            )
            else "PARTIALLY_SETTLED"
        )

        record = SettlementRecord(
            settlement_id=str(uuid4()),
            buy_order_id=match.buy_order_id,
            sell_order_id=match.sell_order_id,
            status=status,
            executed_quantity=executed_quantity,
            buyer_remaining_quantity=buyer_remaining_quantity,
            seller_remaining_quantity=seller_remaining_quantity,
            buyer_status=buyer_status,
            seller_status=seller_status,
        )

        self._records.append(record)

        return record

    def all(self) -> list[SettlementRecord]:
        return list(self._records)

    def get(self, settlement_id: str) -> SettlementRecord:
        for record in self._records:
            if record.settlement_id == settlement_id:
                return record

        raise KeyError(
            f"Settlement not found: {settlement_id}"
        )

    def __len__(self) -> int:
        return len(self._records)