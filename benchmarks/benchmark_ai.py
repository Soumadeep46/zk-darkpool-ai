import json
from pathlib import Path
from time import perf_counter

from src.ai.candidate_router import CandidateRouter
from src.ai.data_generator import generate_synthetic_pairs
from src.ai.feature_engineering import build_feature_frame
from src.models.match import CandidatePair
from src.utils.config import load_config
from src.utils.metrics import summarize


ROOT_DIR = Path(__file__).resolve().parents[1]


# Fractions of the ranked candidate set to test.
SELECTION_FRACTIONS = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
]


def create_candidates(
    n_samples: int,
) -> tuple[list[CandidatePair], list[int]]:
    """
    Generate synthetic candidate pairs and return both:

    1. CandidatePair objects for routing.
    2. Ground-truth labels for precision/recall evaluation.
    """

    pairs = generate_synthetic_pairs(
        n_samples=n_samples,
    )

    features, labels = build_feature_frame(pairs)

    candidates = [
        CandidatePair(
            buy_order_id=f"buy_{index}",
            sell_order_id=f"sell_{index}",
            features=feature_row,
        )
        for index, feature_row in enumerate(
            features.to_dict(orient="records")
        )
    ]

    return candidates, list(labels)


def evaluate_fraction(
    ranked_candidates,
    labels: list[int],
    fraction: float,
) -> dict:
    """
    Evaluate one top-K selection fraction.

    Assumes ranked_candidates are returned in descending
    model-score order.
    """

    total_candidates = len(ranked_candidates)

    selected_count = max(
        1,
        int(total_candidates * fraction),
    )

    selected = ranked_candidates[:selected_count]

    # Candidate IDs are generated as buy_0, buy_1, ...
    # Recover the original index to obtain the ground-truth label.
    selected_indices = [
        int(
            candidate.buy_order_id.replace(
                "buy_",
                "",
            )
        )
        for candidate in selected
    ]

    selected_labels = [
        labels[index]
        for index in selected_indices
    ]

    total_positive = sum(labels)
    selected_positive = sum(selected_labels)

    precision = (
        selected_positive / selected_count
        if selected_count > 0
        else 0.0
    )

    recall = (
        selected_positive / total_positive
        if total_positive > 0
        else 0.0
    )

    eliminated_count = (
        total_candidates - selected_count
    )

    reduction_percentage = (
        eliminated_count / total_candidates
    ) * 100

    return {
        "selection_fraction": fraction,
        "selected_candidates": selected_count,
        "eliminated_candidates": eliminated_count,
        "candidate_reduction_percent": (
            reduction_percentage
        ),
        "selected_valid_matches": (
            selected_positive
        ),
        "total_valid_matches": total_positive,
        "precision": precision,
        "recall": recall,
    }


def benchmark_router() -> dict:
    config = load_config()

    repetitions = config["benchmark"]["repetitions"]

    warmup_iterations = config["benchmark"][
        "warmup_iterations"
    ]

    candidate_count = config["benchmark"]["ai"][
        "candidate_count"
    ]

    router = CandidateRouter()

    candidates, labels = create_candidates(
        candidate_count
    )

    # ==========================================
    # Warmup
    # ==========================================

    for _ in range(warmup_iterations):
        router.rank(candidates)

    # ==========================================
    # Ranking benchmark
    # ==========================================

    ranking_times = []
    last_ranked_candidates = None

    for _ in range(repetitions):

        start_time = perf_counter()

        ranked_candidates = router.rank(
            candidates
        )

        end_time = perf_counter()

        ranking_times.append(
            (end_time - start_time) * 1000
        )

        last_ranked_candidates = (
            ranked_candidates
        )

    # ==========================================
    # Multi-fraction evaluation
    # ==========================================

    fraction_results = {}

    for fraction in SELECTION_FRACTIONS:

        selection_times = []
        evaluations = []

        for _ in range(repetitions):

            start_time = perf_counter()

            total_candidates = len(
                last_ranked_candidates
            )

            selected_count = max(
                1,
                int(
                    total_candidates * fraction
                ),
            )

            selected = (
                last_ranked_candidates[
                    :selected_count
                ]
            )

            end_time = perf_counter()

            selection_times.append(
                (end_time - start_time) * 1000
            )

            evaluation = evaluate_fraction(
                last_ranked_candidates,
                labels,
                fraction,
            )

            evaluations.append(evaluation)

        # Evaluation metrics are deterministic
        # for the same ranked candidate set, so
        # the first result is sufficient.
        evaluation = evaluations[0]

        fraction_key = (
            f"{int(fraction * 100)}%"
        )

        fraction_results[fraction_key] = {
            **evaluation,
            "selection": summarize(
                selection_times
            ),
        }

    return {
        "candidate_count": candidate_count,
        "repetitions": repetitions,
        "ranking": summarize(
            ranking_times
        ),
        "fractions": fraction_results,
    }


def save_results(
    results: dict,
) -> Path:

    config = load_config()

    output_path = (
        ROOT_DIR
        / config["paths"]["results_metrics"]
        / "ai_benchmark.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path


def main():

    results = benchmark_router()

    output_path = save_results(
        results
    )

    print(
        "AI Router Multi-Fraction Benchmark Results"
    )

    print(
        f"\nCandidates: "
        f"{results['candidate_count']}"
    )

    print(
        f"Repetitions: "
        f"{results['repetitions']}"
    )

    # ==========================================
    # Ranking metrics
    # ==========================================

    print("\nRanking")

    for name, value in (
        results["ranking"].items()
    ):
        print(
            f"{name}: "
            f"{value:.3f}"
        )

    # ==========================================
    # Fraction results
    # ==========================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "MULTI-FRACTION RESULTS"
    )

    print(
        "=" * 60
    )

    for fraction, result in (
        results["fractions"].items()
    ):

        print(
            f"\nSelection Fraction: "
            f"{fraction}"
        )

        print(
            f"Selected Candidates: "
            f"{result['selected_candidates']}"
        )

        print(
            f"Eliminated Candidates: "
            f"{result['eliminated_candidates']}"
        )

        print(
            f"Candidate Reduction: "
            f"{result['candidate_reduction_percent']:.2f}%"
        )

        print(
            f"Valid Matches Selected: "
            f"{result['selected_valid_matches']}"
        )

        print(
            f"Total Valid Matches: "
            f"{result['total_valid_matches']}"
        )

        print(
            f"Precision: "
            f"{result['precision']:.4f}"
        )

        print(
            f"Recall: "
            f"{result['recall']:.4f}"
        )

        print(
            "\nSelection Timing:"
        )

        for name, value in (
            result["selection"].items()
        ):
            print(
                f"{name}: "
                f"{value:.4f} ms"
            )

    print(
        f"\nSaved results to: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()