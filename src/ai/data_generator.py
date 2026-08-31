from dataclasses import dataclass
import random

import numpy as np

from src.utils.config import load_config


@dataclass(frozen=True)
class SyntheticPair:
    buy_price: int
    sell_price: int
    buy_volume: int
    sell_volume: int
    buy_age: float
    sell_age: float
    buy_volume_bucket: int
    sell_volume_bucket: int
    buy_liquidity: int
    sell_liquidity: int
    volatility_regime: int
    arrival_intensity: float
    label: int


def _volume_bucket(volume: int, allowed_volumes: list[int]) -> int:
    return allowed_volumes.index(volume)


def generate_synthetic_pairs(
    n_samples: int | None = None,
    seed: int | None = None,
) -> list[SyntheticPair]:
    config = load_config()
    settings = config["synthetic_data"]

    if n_samples is None:
        n_samples = settings["default_pairs"]

    if seed is None:
        seed = settings["seed"]

    random.seed(seed)
    np.random.seed(seed)

    min_price = settings["price"]["min"]
    max_price = settings["price"]["max"]
    allowed_volumes = settings["allowed_volumes"]
    liquidity_buckets = settings["liquidity_buckets"]
    volatility_regimes = settings["volatility_regimes"]

    pairs = []

    for _ in range(n_samples):
        buy_price = random.randint(min_price, max_price)
        sell_price = random.randint(min_price, max_price)

        buy_volume = random.choice(allowed_volumes)
        sell_volume = random.choice(allowed_volumes)

        buy_age = round(random.uniform(0.0, 300.0), 3)
        sell_age = round(random.uniform(0.0, 300.0), 3)

        buy_liquidity = random.randint(0, liquidity_buckets - 1)
        sell_liquidity = random.randint(0, liquidity_buckets - 1)

        volatility_regime = random.randint(
            0,
            volatility_regimes - 1,
        )

        arrival_intensity = round(
            random.uniform(0.0, 1.0),
            6,
        )

        label = int(
            buy_price >= sell_price
            and buy_volume == sell_volume
        )

        pairs.append(
            SyntheticPair(
                buy_price=buy_price,
                sell_price=sell_price,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                buy_age=buy_age,
                sell_age=sell_age,
                buy_volume_bucket=_volume_bucket(
                    buy_volume,
                    allowed_volumes,
                ),
                sell_volume_bucket=_volume_bucket(
                    sell_volume,
                    allowed_volumes,
                ),
                buy_liquidity=buy_liquidity,
                sell_liquidity=sell_liquidity,
                volatility_regime=volatility_regime,
                arrival_intensity=arrival_intensity,
                label=label,
            )
        )

    return pairs