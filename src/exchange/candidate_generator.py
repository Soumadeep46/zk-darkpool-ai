from time import time

from src.models.match import CandidatePair
from src.models.order import PublicOrder


def generate_candidates(
    orders: list[PublicOrder],
) -> list[CandidatePair]:
    buys = [
        order
        for order in orders
        if order.side == "BUY" and order.proof_valid
    ]

    sells = [
        order
        for order in orders
        if order.side == "SELL" and order.proof_valid
    ]

    now = time()
    candidates = []

    for buy in buys:
        for sell in sells:
            if buy.asset != sell.asset:
                continue

            features = {
                "buy_age": max(0.0, now - buy.timestamp),
                "sell_age": max(0.0, now - sell.timestamp),
                "age_difference": abs(
                    buy.timestamp - sell.timestamp
                ),
                "buy_volume_bucket": buy.coarse_volume_bucket,
                "sell_volume_bucket": sell.coarse_volume_bucket,
                "same_volume_bucket": int(
                    buy.coarse_volume_bucket
                    == sell.coarse_volume_bucket
                ),
                "buy_liquidity": buy.liquidity_bucket,
                "sell_liquidity": sell.liquidity_bucket,
                "liquidity_difference": abs(
                    buy.liquidity_bucket
                    - sell.liquidity_bucket
                ),
                "volatility_regime": max(
                    buy.volatility_regime,
                    sell.volatility_regime,
                ),
                "arrival_intensity": (
                    buy.arrival_intensity
                    + sell.arrival_intensity
                ) / 2,
            }

            candidates.append(
                CandidatePair(
                    buy_order_id=buy.order_id,
                    sell_order_id=sell.order_id,
                    features=features,
                )
            )

    return candidates