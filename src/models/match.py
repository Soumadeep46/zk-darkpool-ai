from dataclasses import dataclass


@dataclass(frozen=True)
class CandidatePair:
    buy_order_id: str
    sell_order_id: str
    features: dict
    score: float = 0.0
    explored: bool = False


@dataclass(frozen=True)
class MatchResult:
    buy_order_id: str
    sell_order_id: str
    valid: bool
    verification_time_ms: float