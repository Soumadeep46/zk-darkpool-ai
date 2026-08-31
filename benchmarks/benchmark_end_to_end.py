import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import matplotlib.pyplot as plt

from src.ai.candidate_router import CandidateRouter
from src.crypto.commitments import poseidon_commit, random_nonce
from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier
from src.exchange.candidate_generator import generate_candidates
from src.exchange.matching_engine import MatchingEngine
from src.exchange.private_order_book import PrivateOrderBook
from src.exchange.settlement import SettlementEngine
from src.models.order import PrivateOrder, PublicOrder
from src.utils.config import load_config
from src.utils.metrics import summarize


ROOT_DIR = Path(__file__).resolve().parents[1]

CPU_THREADS = os.cpu_count() or 4
PARALLEL_ZK_WORKERS = min(8, CPU_THREADS)


def create_private_order(
    side: str,
    price: int,
    volume: int,
) -> PrivateOrder:

    return PrivateOrder(
        order_id=str(uuid4()),
        side=side,
        asset="DEMO_ASSET",
        private_price=price,
        private_volume=volume,
        price_nonce=random_nonce(),
        volume_nonce=random_nonce(),
    )


def create_public_order(
    order: PrivateOrder,
    prover: SnarkProver,
    verifier: SnarkVerifier,
    volume_bucket: int,
    liquidity_bucket: int,
    volatility_regime: int,
    arrival_intensity: float,
) -> PublicOrder:

    price_commitment = poseidon_commit(
        order.private_price,
        order.price_nonce,
    )

    volume_commitment = poseidon_commit(
        order.private_volume,
        order.volume_nonce,
    )

    proof_result = prover.prove(
        {
            "price": order.private_price,
            "volume": order.private_volume,
            "price_nonce": order.price_nonce,
            "volume_nonce": order.volume_nonce,
            "price_commitment": price_commitment,
            "volume_commitment": volume_commitment,
        }
    )

    verification_result = verifier.verify(
        proof_result.proof,
        proof_result.public_signals,
    )

    if not verification_result["valid"]:
        raise RuntimeError(
            "Order proof verification failed"
        )

    return PublicOrder(
        order_id=order.order_id,
        side=order.side,
        asset=order.asset,
        coarse_volume_bucket=volume_bucket,
        liquidity_bucket=liquidity_bucket,
        volatility_regime=volatility_regime,
        arrival_intensity=arrival_intensity,
        price_commitment=price_commitment,
        volume_commitment=volume_commitment,
        proof_valid=True,
        timestamp=order.timestamp,
    )


def build_match_inputs(
    buy_order: PrivateOrder,
    sell_order: PrivateOrder,
) -> dict:

    return {
        "buy_price": buy_order.private_price,
        "sell_price": sell_order.private_price,
        "buy_volume": buy_order.private_volume,
        "sell_volume": sell_order.private_volume,

        "buy_price_nonce": buy_order.price_nonce,
        "sell_price_nonce": sell_order.price_nonce,

        "buy_volume_nonce": buy_order.volume_nonce,
        "sell_volume_nonce": sell_order.volume_nonce,

        "buy_price_commitment": poseidon_commit(
            buy_order.private_price,
            buy_order.price_nonce,
        ),

        "sell_price_commitment": poseidon_commit(
            sell_order.private_price,
            sell_order.price_nonce,
        ),

        "buy_volume_commitment": poseidon_commit(
            buy_order.private_volume,
            buy_order.volume_nonce,
        ),

        "sell_volume_commitment": poseidon_commit(
            sell_order.private_volume,
            sell_order.volume_nonce,
        ),
    }


def create_market(
    order_prover: SnarkProver,
    order_verifier: SnarkVerifier,
) -> tuple[
    PrivateOrderBook,
    dict[str, PrivateOrder],
]:

    order_book = PrivateOrderBook()

    private_orders = {}

    buy_prices = [
        950,
        975,
        990,
        1000,
        1010,
        1025,
        1040,
        1050,
        1075,
        1100,
    ]

    buy_volumes = [
        100,
        200,
        300,
        400,
        500,
        500,
        600,
        700,
        800,
        1000,
    ]

    for index in range(
        len(buy_prices)
    ):

        buy_private = create_private_order(
            side="BUY",
            price=buy_prices[index],
            volume=buy_volumes[index],
        )

        buy_public = create_public_order(
            order=buy_private,
            prover=order_prover,
            verifier=order_verifier,

            volume_bucket=min(
                5,
                max(
                    1,
                    buy_volumes[index] // 200,
                ),
            ),

            liquidity_bucket=(
                index % 3
            ) + 1,

            volatility_regime=(
                index % 2
            ) + 1,

            arrival_intensity=(
                0.50
                + index * 0.03
            ),
        )

        order_book.add(
            buy_public
        )

        private_orders[
            buy_private.order_id
        ] = buy_private

    sell_prices = [
        900,
        940,
        960,
        980,
        1000,
        1010,
        1030,
        1060,
        1080,
        1120,
    ]

    sell_volumes = [
        100,
        200,
        300,
        400,
        500,
        500,
        600,
        700,
        800,
        1000,
    ]

    for index in range(
        len(sell_prices)
    ):

        sell_private = create_private_order(
            side="SELL",
            price=sell_prices[index],
            volume=sell_volumes[index],
        )

        sell_public = create_public_order(
            order=sell_private,
            prover=order_prover,
            verifier=order_verifier,

            volume_bucket=min(
                5,
                max(
                    1,
                    sell_volumes[index] // 200,
                ),
            ),

            liquidity_bucket=(
                (index + 1) % 3
            ) + 1,

            volatility_regime=(
                index % 2
            ) + 1,

            arrival_intensity=(
                0.45
                + index * 0.03
            ),
        )

        order_book.add(
            sell_public
        )

        private_orders[
            sell_private.order_id
        ] = sell_private

    return (
        order_book,
        private_orders,
    )


def build_proof_inputs(
    candidates,
    private_orders: dict[str, PrivateOrder],
) -> dict:

    proof_inputs = {}

    for candidate in candidates:

        buy_order = private_orders[
            candidate.buy_order_id
        ]

        sell_order = private_orders[
            candidate.sell_order_id
        ]

        key = (
            candidate.buy_order_id,
            candidate.sell_order_id,
        )

        proof_inputs[
            key
        ] = build_match_inputs(
            buy_order,
            sell_order,
        )

    return proof_inputs


def execute_matching(
    candidates,
    proof_inputs: dict,
) -> dict:

    matching_engine = MatchingEngine(
        max_workers=PARALLEL_ZK_WORKERS
    )

    matching_start = perf_counter()

    match_results = matching_engine.match(
        candidates,
        proof_inputs,
    )

    matching_time_ms = (
        perf_counter()
        - matching_start
    ) * 1000

    settlement_engine = SettlementEngine()

    settlements = []

    for result in match_results:

        if result.valid:

            settlements.append(
                settlement_engine.settle(
                    result
                )
            )

    valid_matches = sum(
        result.valid
        for result in match_results
    )

    return {
        "match_results": match_results,
        "valid_matches": valid_matches,
        "settlements": len(settlements),
        "matching_time_ms": matching_time_ms,
    }


def select_top_fraction(
    router: CandidateRouter,
    candidates,
    selection_fraction: float,
):

    if not 0 < selection_fraction <= 1:

        raise ValueError(
            "selection_fraction must be "
            "between 0 and 1."
        )

    ranked_candidates = router.rank(
        candidates
    )

    selection_count = max(
        1,
        int(
            len(ranked_candidates)
            * selection_fraction
        ),
    )

    return ranked_candidates[
        :selection_count
    ]


def filter_candidates_before_zk(
    candidates,
    private_orders: dict[str, PrivateOrder],
):

    filtered = []

    for candidate in candidates:

        buy_order = private_orders[
            candidate.buy_order_id
        ]

        sell_order = private_orders[
            candidate.sell_order_id
        ]

        if (
            buy_order.private_price
            >= sell_order.private_price
            and buy_order.private_volume
            >= sell_order.private_volume
        ):

            filtered.append(
                candidate
            )

    return filtered


def prepare_market() -> dict:

    order_prover = SnarkProver(
        "order_validity"
    )

    order_verifier = SnarkVerifier(
        "order_validity"
    )

    preparation_start = perf_counter()

    order_book, private_orders = create_market(
        order_prover,
        order_verifier,
    )

    candidates = generate_candidates(
        order_book.all()
    )

    preparation_time_ms = (
        perf_counter()
        - preparation_start
    ) * 1000

    return {
        "order_book": order_book,
        "private_orders": private_orders,
        "candidates": candidates,
        "market_preparation_time_ms": (
            preparation_time_ms
        ),
    }


def run_baseline_pipeline(
    market: dict,
) -> dict:

    candidates = market[
        "candidates"
    ]

    private_orders = market[
        "private_orders"
    ]

    zk_candidates = filter_candidates_before_zk(
        candidates,
        private_orders,
    )

    proof_inputs = build_proof_inputs(
        zk_candidates,
        private_orders,
    )

    matching_result = execute_matching(
        zk_candidates,
        proof_inputs,
    )

    return {
        "orders": len(
            market["order_book"]
        ),

        "candidates": len(
            candidates
        ),

        "candidates_sent_to_zk": len(
            zk_candidates
        ),

        "candidates_filtered_before_zk": (
            len(candidates)
            - len(zk_candidates)
        ),

        "valid_matches": (
            matching_result[
                "valid_matches"
            ]
        ),

        "settlements": (
            matching_result[
                "settlements"
            ]
        ),

        "matching_time_ms": (
            matching_result[
                "matching_time_ms"
            ]
        ),
    }


def run_ai_pipeline(
    market: dict,
    selection_fraction: float,
) -> dict:

    candidates = market[
        "candidates"
    ]

    private_orders = market[
        "private_orders"
    ]

    router = CandidateRouter()

    ranking_start = perf_counter()

    selected_candidates = select_top_fraction(
        router,
        candidates,
        selection_fraction,
    )

    ranking_time_ms = (
        perf_counter()
        - ranking_start
    ) * 1000

    zk_candidates = filter_candidates_before_zk(
        selected_candidates,
        private_orders,
    )

    proof_inputs = build_proof_inputs(
        zk_candidates,
        private_orders,
    )

    matching_result = execute_matching(
        zk_candidates,
        proof_inputs,
    )

    return {
        "orders": len(
            market["order_book"]
        ),

        "candidates": len(
            candidates
        ),

        "ai_selected": len(
            selected_candidates
        ),

        "ai_eliminated": (
            len(candidates)
            - len(selected_candidates)
        ),

        "candidates_sent_to_zk": len(
            zk_candidates
        ),

        "candidates_filtered_before_zk": (
            len(selected_candidates)
            - len(zk_candidates)
        ),

        "selection_fraction": (
            selection_fraction
        ),

        "ai_ranking_time_ms": (
            ranking_time_ms
        ),

        "valid_matches": (
            matching_result[
                "valid_matches"
            ]
        ),

        "settlements": (
            matching_result[
                "settlements"
            ]
        ),

        "matching_time_ms": (
            matching_result[
                "matching_time_ms"
            ]
        ),
    }


def benchmark_end_to_end() -> dict:

    config = load_config()

    repetitions = config[
        "benchmark"
    ][
        "repetitions"
    ]

    warmup_iterations = config[
        "benchmark"
    ][
        "warmup_iterations"
    ]

    selection_fractions = [
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

    print()
    print("=" * 60)
    print("AI-ZK END-TO-END BENCHMARK")
    print("=" * 60)

    print()
    print(
        f"CPU Threads: "
        f"{CPU_THREADS}"
    )

    print(
        f"Parallel ZK Workers: "
        f"{PARALLEL_ZK_WORKERS}"
    )

    print(
        f"Warmup iterations: "
        f"{warmup_iterations}"
    )

    print(
        f"Benchmark repetitions: "
        f"{repetitions}"
    )

    print(
        f"Selection fractions: "
        f"{len(selection_fractions)}"
    )

    print()
    print("Preparing market...")

    market = prepare_market()

    print(
        f"Market preparation completed in "
        f"{market['market_preparation_time_ms'] / 1000:.2f} "
        f"seconds"
    )

    print()
    print("=" * 60)
    print("WARMUP")
    print("=" * 60)

    for _ in range(
        warmup_iterations
    ):

        run_baseline_pipeline(
            market
        )

        for fraction in (
            selection_fractions
        ):

            run_ai_pipeline(
                market,
                fraction,
            )

    print()
    print("=" * 60)
    print("BASELINE BENCHMARK")
    print("=" * 60)

    baseline_times = []

    baseline_results = []

    for run_number in range(
        1,
        repetitions + 1,
    ):

        print(
            f"Baseline run "
            f"{run_number}/{repetitions}...",
            flush=True,
        )

        start = perf_counter()

        result = run_baseline_pipeline(
            market
        )

        elapsed_ms = (
            perf_counter()
            - start
        ) * 1000

        baseline_times.append(
            elapsed_ms
        )

        baseline_results.append(
            result
        )

        print(
            f"Completed in "
            f"{elapsed_ms / 1000:.2f} "
            f"seconds"
        )

    baseline_final = (
        baseline_results[-1]
    )

    baseline_valid_matches = (
        baseline_final[
            "valid_matches"
        ]
    )

    baseline_zk_work = (
        baseline_final[
            "candidates_sent_to_zk"
        ]
    )

    baseline_mean_ms = summarize(
        baseline_times
    )[
        "mean_ms"
    ]

    print()
    print("=" * 60)
    print("AI + ZK BENCHMARK")
    print("=" * 60)

    ai_results = {}

    for fraction in (
        selection_fractions
    ):

        fraction_label = (
            f"{int(fraction * 100)}%"
        )

        print()
        print(
            f"Selection Fraction: "
            f"{fraction_label}"
        )

        pipeline_times = []

        ranking_times = []

        matching_times = []

        selected_counts = []

        eliminated_counts = []

        zk_candidate_counts = []

        filtered_before_zk_counts = []

        valid_match_counts = []

        settlement_counts = []

        for run_number in range(
            1,
            repetitions + 1,
        ):

            print(
                f"AI {fraction_label} "
                f"run "
                f"{run_number}/{repetitions}...",
                flush=True,
            )

            start = perf_counter()

            result = run_ai_pipeline(
                market,
                fraction,
            )

            elapsed_ms = (
                perf_counter()
                - start
            ) * 1000

            pipeline_times.append(
                elapsed_ms
            )

            ranking_times.append(
                result[
                    "ai_ranking_time_ms"
                ]
            )

            matching_times.append(
                result[
                    "matching_time_ms"
                ]
            )

            selected_counts.append(
                result[
                    "ai_selected"
                ]
            )

            eliminated_counts.append(
                result[
                    "ai_eliminated"
                ]
            )

            zk_candidate_counts.append(
                result[
                    "candidates_sent_to_zk"
                ]
            )

            filtered_before_zk_counts.append(
                result[
                    "candidates_filtered_before_zk"
                ]
            )

            valid_match_counts.append(
                result[
                    "valid_matches"
                ]
            )

            settlement_counts.append(
                result[
                    "settlements"
                ]
            )

            print(
                f"Completed in "
                f"{elapsed_ms / 1000:.2f} "
                f"seconds"
            )

        mean_selected = (
            sum(selected_counts)
            / len(selected_counts)
        )

        mean_eliminated = (
            sum(eliminated_counts)
            / len(eliminated_counts)
        )

        mean_zk_candidates = (
            sum(zk_candidate_counts)
            / len(zk_candidate_counts)
        )

        mean_filtered_before_zk = (
            sum(filtered_before_zk_counts)
            / len(filtered_before_zk_counts)
        )

        mean_valid_matches = (
            sum(valid_match_counts)
            / len(valid_match_counts)
        )

        mean_settlements = (
            sum(settlement_counts)
            / len(settlement_counts)
        )

        total_candidates = len(
            market[
                "candidates"
            ]
        )

        candidate_reduction = (
            mean_eliminated
            / total_candidates
        ) * 100

        if baseline_zk_work > 0:

            zk_work_reduction = (
                (
                    baseline_zk_work
                    - mean_zk_candidates
                )
                / baseline_zk_work
            ) * 100

        else:

            zk_work_reduction = 0.0

        if baseline_valid_matches > 0:

            recall = (
                mean_valid_matches
                / baseline_valid_matches
            )

        else:

            recall = 0.0

        if mean_zk_candidates > 0:

            precision = (
                mean_valid_matches
                / mean_zk_candidates
            )

        else:

            precision = 0.0

        ai_mean_ms = summarize(
            pipeline_times
        )[
            "mean_ms"
        ]

        latency_reduction = (
            (
                baseline_mean_ms
                - ai_mean_ms
            )
            / baseline_mean_ms
        ) * 100

        ai_results[
            fraction_label
        ] = {
            "selection_fraction": (
                fraction
            ),

            "pipeline_latency": summarize(
                pipeline_times
            ),

            "ai_ranking_latency": summarize(
                ranking_times
            ),

            "zk_matching_latency": summarize(
                matching_times
            ),

            "mean_candidates_processed": (
                mean_selected
            ),

            "mean_candidates_eliminated": (
                mean_eliminated
            ),

            "mean_candidates_sent_to_zk": (
                mean_zk_candidates
            ),

            "mean_candidates_filtered_before_zk": (
                mean_filtered_before_zk
            ),

            "candidate_reduction_percent": (
                candidate_reduction
            ),

            "zk_work_reduction_percent": (
                zk_work_reduction
            ),

            "mean_valid_matches": (
                mean_valid_matches
            ),

            "recall": (
                recall
            ),

            "precision": (
                precision
            ),

            "mean_settlements": (
                mean_settlements
            ),

            "latency_reduction_percent": (
                latency_reduction
            ),
        }

    return {
        "cpu_threads": (
            CPU_THREADS
        ),

        "parallel_zk_workers": (
            PARALLEL_ZK_WORKERS
        ),

        "market_preparation_time_ms": (
            market[
                "market_preparation_time_ms"
            ]
        ),

        "repetitions": (
            repetitions
        ),

        "baseline": {
            "pipeline_latency": summarize(
                baseline_times
            ),

            "final_run": (
                baseline_final
            ),
        },

        "ai_zk_pipeline": (
            ai_results
        ),
    }


def save_results(
    results: dict,
) -> Path:

    config = load_config()

    output_path = (
        ROOT_DIR
        / config["paths"][
            "results_metrics"
        ]
        / "end_to_end_benchmark.json"
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


def generate_graphs(
    results: dict,
) -> list[Path]:

    figures_dir = (
        ROOT_DIR
        / "results"
        / "figures"
    )

    figures_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    ai_results = results[
        "ai_zk_pipeline"
    ]

    if not ai_results:

        raise RuntimeError(
            "No AI benchmark results "
            "available for graph generation."
        )

    required_keys = [
        "selection_fraction",
        "pipeline_latency",
        "ai_ranking_latency",
        "mean_candidates_processed",
        "candidate_reduction_percent",
        "zk_work_reduction_percent",
        "recall",
    ]

    fractions = []
    routing_times = []
    recalls = []
    candidate_reductions = []
    zk_work_reductions = []
    candidate_counts = []

    for label, result in ai_results.items():

        for key in required_keys:

            if key not in result:

                raise KeyError(
                    f"\nMissing required key '{key}' "
                    f"for selection fraction {label}.\n\n"
                    f"Available keys:\n"
                    f"{list(result.keys())}"
                )

        if (
            "mean_ms"
            not in result[
                "ai_ranking_latency"
            ]
        ):

            raise KeyError(
                f"\nMissing 'mean_ms' inside "
                f"'ai_ranking_latency' "
                f"for selection fraction {label}."
            )

        fractions.append(
            result[
                "selection_fraction"
            ]
        )

        routing_times.append(
            result[
                "ai_ranking_latency"
            ][
                "mean_ms"
            ]
        )

        recalls.append(
            result[
                "recall"
            ]
        )

        candidate_reductions.append(
            result[
                "candidate_reduction_percent"
            ]
        )

        zk_work_reductions.append(
            result[
                "zk_work_reduction_percent"
            ]
        )

        candidate_counts.append(
            int(
                result[
                    "mean_candidates_processed"
                ]
            )
        )

    saved_paths = []

    graph1_path = (
        figures_dir
        / "candidate_count_vs_ai_routing_time.png"
    )

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        candidate_counts,
        routing_times,
        marker="o",
    )

    plt.xlabel(
        "Candidates Processed"
    )

    plt.ylabel(
        "AI Routing Time (ms)"
    )

    plt.title(
        "Candidate Count vs AI Routing Time"
    )

    plt.grid(
        True
    )

    plt.tight_layout()

    plt.savefig(
        graph1_path,
        dpi=300,
    )

    plt.close()

    if not graph1_path.exists():

        raise RuntimeError(
            f"Failed to generate "
            f"{graph1_path}"
        )

    saved_paths.append(
        graph1_path
    )

    graph2_path = (
        figures_dir
        / "selection_fraction_vs_valid_match_recall.png"
    )

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        [
            fraction * 100
            for fraction in fractions
        ],
        [
            recall * 100
            for recall in recalls
        ],
        marker="o",
    )

    plt.xlabel(
        "AI Selection Fraction (%)"
    )

    plt.ylabel(
        "Valid Match Recall (%)"
    )

    plt.title(
        "Selection Fraction vs Valid Match Recall"
    )

    plt.grid(
        True
    )

    plt.tight_layout()

    plt.savefig(
        graph2_path,
        dpi=300,
    )

    plt.close()

    if not graph2_path.exists():

        raise RuntimeError(
            f"Failed to generate "
            f"{graph2_path}"
        )

    saved_paths.append(
        graph2_path
    )

    graph3_path = (
        figures_dir
        / "ai_candidate_reduction_vs_zk_work.png"
    )

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        candidate_reductions,
        zk_work_reductions,
        marker="o",
    )

    plt.xlabel(
        "AI Candidate Reduction (%)"
    )

    plt.ylabel(
        "ZK Verification Work Reduction (%)"
    )

    plt.title(
        "AI Candidate Reduction vs ZK Verification Work"
    )

    plt.grid(
        True
    )

    plt.tight_layout()

    plt.savefig(
        graph3_path,
        dpi=300,
    )

    plt.close()

    if not graph3_path.exists():

        raise RuntimeError(
            f"Failed to generate "
            f"{graph3_path}"
        )

    saved_paths.append(
        graph3_path
    )

    return saved_paths


def main():

    results = benchmark_end_to_end()

    output_path = save_results(
        results
    )

    print()
    print("=" * 60)
    print(
        "AI-ZK END-TO-END "
        "BENCHMARK RESULTS"
    )
    print("=" * 60)

    print()

    print(
        f"CPU Threads: "
        f"{results['cpu_threads']}"
    )

    print(
        f"Parallel ZK Workers: "
        f"{results['parallel_zk_workers']}"
    )

    print(
        f"Market Preparation Time: "
        f"{results['market_preparation_time_ms']:.2f} ms"
    )

    print()

    print("=" * 60)
    print("BASELINE")
    print("=" * 60)

    baseline = results[
        "baseline"
    ]

    for name, value in (
        baseline[
            "pipeline_latency"
        ].items()
    ):

        print(
            f"{name}: "
            f"{value:.3f} ms"
        )

    print()

    for name, value in (
        baseline[
            "final_run"
        ].items()
    ):

        print(
            f"{name}: {value}"
        )

    print()

    print("=" * 60)
    print(
        "AI + ZK PIPELINE"
    )
    print("=" * 60)

    for label, result in (
        results[
            "ai_zk_pipeline"
        ].items()
    ):

        print()

        print(
            f"Selection Fraction: "
            f"{label}"
        )

        print(
            f"AI Selected: "
            f"{result['mean_candidates_processed']:.0f}"
        )

        print(
            f"AI Eliminated: "
            f"{result['mean_candidates_eliminated']:.0f}"
        )

        print(
            f"Candidate Reduction: "
            f"{result['candidate_reduction_percent']:.2f}%"
        )

        print(
            f"Sent to ZK: "
            f"{result['mean_candidates_sent_to_zk']:.0f}"
        )

        print(
            f"Filtered Before ZK: "
            f"{result['mean_candidates_filtered_before_zk']:.0f}"
        )

        print(
            f"ZK Work Reduction: "
            f"{result['zk_work_reduction_percent']:.2f}%"
        )

        print(
            f"Valid Matches: "
            f"{result['mean_valid_matches']:.2f}"
        )

        print(
            f"Recall: "
            f"{result['recall']:.4f}"
        )

        print(
            f"Precision: "
            f"{result['precision']:.4f}"
        )

        print(
            f"Latency Reduction: "
            f"{result['latency_reduction_percent']:.2f}%"
        )

        print()
        print(
            "Pipeline Timing:"
        )

        for name, value in (
            result[
                "pipeline_latency"
            ].items()
        ):

            print(
                f"{name}: "
                f"{value:.3f} ms"
            )

        print()
        print(
            "AI Ranking Timing:"
        )

        for name, value in (
            result[
                "ai_ranking_latency"
            ].items()
        ):

            print(
                f"{name}: "
                f"{value:.3f} ms"
            )

        print()
        print(
            "ZK Matching Timing:"
        )

        for name, value in (
            result[
                "zk_matching_latency"
            ].items()
        ):

            print(
                f"{name}: "
                f"{value:.3f} ms"
            )

    print()

    print(
        f"Saved results to: "
        f"{output_path}"
    )

    print()
    print(
        "Generating graphs..."
    )

    graph_paths = generate_graphs(
        results
    )

    print()
    print(
        "Graphs generated successfully:"
    )

    for graph_path in graph_paths:

        print(
            f"  {graph_path}"
        )


if __name__ == "__main__":
    main()