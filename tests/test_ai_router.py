from src.ai.data_generator import generate_synthetic_pairs
from src.ai.feature_engineering import build_feature_frame
from src.utils.config import load_config


def test_private_values_are_not_features():
    pairs = generate_synthetic_pairs(
        n_samples=100,
        seed=42,
    )

    features, labels = build_feature_frame(pairs)

    config = load_config()
    forbidden = set(
        config["privacy"]["forbidden_ai_features"]
    )

    assert not (
        set(features.columns) & forbidden
    )

    assert len(features) == 100
    assert len(labels) == 100


def test_feature_frame_contains_expected_columns():
    pairs = generate_synthetic_pairs(
        n_samples=10,
        seed=42,
    )

    features, _ = build_feature_frame(pairs)

    expected_columns = {
        "buy_age",
        "sell_age",
        "age_difference",
        "buy_volume_bucket",
        "sell_volume_bucket",
        "same_volume_bucket",
        "buy_liquidity",
        "sell_liquidity",
        "liquidity_difference",
        "volatility_regime",
        "arrival_intensity",
    }

    assert set(features.columns) == expected_columns


def test_labels_are_binary():
    pairs = generate_synthetic_pairs(
        n_samples=100,
        seed=42,
    )

    _, labels = build_feature_frame(pairs)

    assert set(labels.unique()).issubset({0, 1})


def test_feature_generation_is_reproducible():
    pairs_1 = generate_synthetic_pairs(
        n_samples=50,
        seed=42,
    )

    pairs_2 = generate_synthetic_pairs(
        n_samples=50,
        seed=42,
    )

    features_1, labels_1 = build_feature_frame(pairs_1)
    features_2, labels_2 = build_feature_frame(pairs_2)

    assert features_1.equals(features_2)
    assert labels_1.equals(labels_2)