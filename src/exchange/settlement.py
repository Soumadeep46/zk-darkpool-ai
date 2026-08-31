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
    timestamp: float = field(default_factory=time)


class SettlementEngine:
    def __init__(self):
        self._records: list[SettlementRecord] = []

    def settle(self, match: MatchResult) -> SettlementRecord:
        if not match.valid:
            raise ValueError("Cannot settle an invalid match")

        record = SettlementRecord(
            settlement_id=str(uuid4()),
            buy_order_id=match.buy_order_id,
            sell_order_id=match.sell_order_id,
            status="SETTLED",
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