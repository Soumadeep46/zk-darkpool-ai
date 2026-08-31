from pathlib import Path
import json

import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.ai.data_generator import generate_synthetic_pairs
from src.ai.feature_engineering import build_feature_frame
from src.utils.config import load_config


ROOT_DIR = Path(__file__).resolve().parents[2]


def precision_at_k(y_true, scores, fraction: float) -> float:
    k = max(1, int(len(scores) * fraction))
    ranked_indices = scores.argsort()[::-1][:k]
    return float(y_true.iloc[ranked_indices].mean())


def recall_at_k(y_true, scores, fraction: float) -> float:
    k = max(1, int(len(scores) * fraction))
    ranked_indices = scores.argsort()[::-1][:k]

    positives = int(y_true.sum())

    if positives == 0:
        return 0.0

    return float(y_true.iloc[ranked_indices].sum() / positives)


def train_router() -> dict:
    config = load_config()
    ai_config = config["ai"]

    pairs = generate_synthetic_pairs(
        n_samples=ai_config["training"]["n_samples"],
        seed=ai_config["random_state"],
    )

    features, labels = build_feature_frame(pairs)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=ai_config["training"]["test_size"],
        random_state=ai_config["random_state"],
        stratify=labels,
    )

    model_config = ai_config["model"]

    model = GradientBoostingClassifier(
        n_estimators=model_config["n_estimators"],
        learning_rate=model_config["learning_rate"],
        max_depth=model_config["max_depth"],
        random_state=ai_config["random_state"],
    )

    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )

    metrics = {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "average_precision": float(
            average_precision_score(y_test, probabilities)
        ),
    }

    for fraction in config["benchmark"]["ai"]["top_fractions"]:
        key = int(fraction * 100)

        metrics[f"precision_at_{key}"] = precision_at_k(
            y_test,
            probabilities,
            fraction,
        )

        metrics[f"recall_at_{key}"] = recall_at_k(
            y_test,
            probabilities,
            fraction,
        )

    model_path = ROOT_DIR / ai_config["model_path"]
    model_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "feature_columns": list(features.columns),
        },
        model_path,
    )

    metrics_path = (
        ROOT_DIR
        / config["paths"]["results_metrics"]
        / "router_metrics.json"
    )

    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    metrics_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    return metrics


if __name__ == "__main__":
    results = train_router()

    for name, value in results.items():
        print(f"{name}: {value:.4f}")