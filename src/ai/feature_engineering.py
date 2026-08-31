import pandas as pd

from src.ai.data_generator import SyntheticPair
from src.utils.config import load_config


def build_feature_frame(
    pairs: list[SyntheticPair],
) -> tuple[pd.DataFrame, pd.Series]:
    config = load_config()

    forbidden = set(
        config["privacy"]["forbidden_ai_features"]
    )

    rows = []
    labels = []

    for pair in pairs:
        row = {
            "buy_age": pair.buy_age,
            "sell_age": pair.sell_age,
            "age_difference": abs(
                pair.buy_age - pair.sell_age
            ),
            "buy_volume_bucket": pair.buy_volume_bucket,
            "sell_volume_bucket": pair.sell_volume_bucket,
            "same_volume_bucket": int(
                pair.buy_volume_bucket
                == pair.sell_volume_bucket
            ),
            "buy_liquidity": pair.buy_liquidity,
            "sell_liquidity": pair.sell_liquidity,
            "liquidity_difference": abs(
                pair.buy_liquidity
                - pair.sell_liquidity
            ),
            "volatility_regime": pair.volatility_regime,
            "arrival_intensity": pair.arrival_intensity,
        }

        rows.append(row)
        labels.append(pair.label)

    features = pd.DataFrame(rows)

    leaked_features = (
        set(features.columns)
        .intersection(forbidden)
    )

    if leaked_features:
        raise ValueError(
            f"Forbidden AI features detected: "
            f"{sorted(leaked_features)}"
        )

    return features, pd.Series(
        labels,
        name="label",
    )