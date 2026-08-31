from dataclasses import dataclass, field
from typing import Literal
import time

Side = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class PrivateOrder:
    order_id: str
    side: Side
    asset: str
    private_price: int
    private_volume: int
    price_nonce: int
    volume_nonce: int
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class PublicOrder:
    order_id: str
    side: Side
    asset: str

    coarse_volume_bucket: int
    liquidity_bucket: int
    volatility_regime: int
    arrival_intensity: float

    price_commitment: str
    volume_commitment: str

    proof_valid: bool
    timestamp: float

    def as_exchange_record(self) -> dict:
        return {
            "order_id": self.order_id,
            "side": self.side,
            "asset": self.asset,
            "coarse_volume_bucket": self.coarse_volume_bucket,
            "liquidity_bucket": self.liquidity_bucket,
            "volatility_regime": self.volatility_regime,
            "arrival_intensity": self.arrival_intensity,
            "price_commitment": self.price_commitment,
            "volume_commitment": self.volume_commitment,
            "proof_valid": self.proof_valid,
            "timestamp": self.timestamp,
        }