from pathlib import Path
import random

import joblib
import pandas as pd

from src.models.match import CandidatePair
from src.utils.config import load_config


ROOT_DIR = Path(__file__).resolve().parents[2]


class CandidateRouter:
    def __init__(self):
        config = load_config()
        self.config = config

        model_path = (
            ROOT_DIR
            / config["ai"]["model_path"]
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained router model not found: {model_path}"
            )

        artifact = joblib.load(model_path)

        self.model = artifact["model"]
        self.feature_columns = artifact["feature_columns"]
        self.random = random.Random(
            config["ai"]["random_state"]
        )

    def rank(
        self,
        candidates: list[CandidatePair],
    ) -> list[CandidatePair]:
        if not candidates:
            return []

        features = pd.DataFrame(
            [
                candidate.features
                for candidate in candidates
            ]
        )

        missing = (
            set(self.feature_columns)
            - set(features.columns)
        )

        if missing:
            raise ValueError(
                f"Missing candidate features: {sorted(missing)}"
            )

        features = features[self.feature_columns]

        scores = self.model.predict_proba(features)[:, 1]

        ranked = [
            CandidatePair(
                buy_order_id=candidate.buy_order_id,
                sell_order_id=candidate.sell_order_id,
                features=candidate.features,
                score=float(score),
                explored=False,
            )
            for candidate, score in zip(
                candidates,
                scores,
            )
        ]

        return sorted(
            ranked,
            key=lambda candidate: candidate.score,
            reverse=True,
        )

    def select(
        self,
        candidates: list[CandidatePair],
    ) -> list[CandidatePair]:
        if not candidates:
            return []

        ranked = self.rank(candidates)

        routing = self.config["ai"]["routing"]

        top_count = max(
            1,
            int(
                len(ranked)
                * routing["top_fraction"]
            ),
        )

        selected = ranked[:top_count]
        remaining = ranked[top_count:]

        exploration_count = min(
            len(remaining),
            int(
                len(ranked)
                * routing["exploration_fraction"]
            ),
        )

        if exploration_count > 0:
            explored = self.random.sample(
                remaining,
                exploration_count,
            )

            explored = [
                CandidatePair(
                    buy_order_id=candidate.buy_order_id,
                    sell_order_id=candidate.sell_order_id,
                    features=candidate.features,
                    score=candidate.score,
                    explored=True,
                )
                for candidate in explored
            ]

            selected.extend(explored)

        return sorted(
            selected,
            key=lambda candidate: candidate.score,
            reverse=True,
        )