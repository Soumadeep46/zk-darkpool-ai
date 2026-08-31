import json
from pathlib import Path

import matplotlib.pyplot as plt

from src.utils.config import load_config


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_json(filename: str) -> dict:
    config = load_config()

    path = (
        ROOT_DIR
        / config["paths"]["results_metrics"]
        / filename
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark result not found: {path}"
        )

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def create_output_dir() -> Path:
    config = load_config()

    output_dir = (
        ROOT_DIR
        / config["paths"]["results_plots"]
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return output_dir


def plot_zk_results(
    results: dict,
    output_dir: Path,
) -> None:
    categories = [
        "witness_generation",
        "proof_generation",
        "verification",
    ]

    labels = [
        "Witness",
        "Proof",
        "Verification",
    ]

    values = [
        results[category]["mean_ms"]
        for category in categories
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(labels, values)

    plt.ylabel("Mean latency (ms)")
    plt.title("ZK Pipeline Latency")

    plt.tight_layout()

    plt.savefig(
        output_dir / "zk_latency.png",
        dpi=150,
    )

    plt.close()


def plot_ai_results(
    results: dict,
    output_dir: Path,
) -> None:
    labels = [
        "Ranking",
        "Selection",
    ]

    values = [
        results["ranking"]["mean_ms"],
        results["selection"]["mean_ms"],
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(labels, values)

    plt.ylabel("Mean latency (ms)")
    plt.title("AI Router Latency")

    plt.tight_layout()

    plt.savefig(
        output_dir / "ai_latency.png",
        dpi=150,
    )

    plt.close()


def plot_end_to_end_results(
    results: dict,
    output_dir: Path,
) -> None:
    metrics = results["pipeline_latency"]

    labels = [
        "Mean",
        "Median",
        "P95",
    ]

    values = [
        metrics["mean_ms"],
        metrics["median_ms"],
        metrics["p95_ms"],
    ]

    plt.figure(figsize=(8, 5))

    plt.bar(labels, values)

    plt.ylabel("Latency (ms)")
    plt.title("End-to-End Pipeline Latency")

    plt.tight_layout()

    plt.savefig(
        output_dir / "end_to_end_latency.png",
        dpi=150,
    )

    plt.close()


def main():
    output_dir = create_output_dir()

    zk_results = load_json(
        "zk_benchmark.json"
    )

    ai_results = load_json(
        "ai_benchmark.json"
    )

    end_to_end_results = load_json(
        "end_to_end_benchmark.json"
    )

    plot_zk_results(
        zk_results,
        output_dir,
    )

    plot_ai_results(
        ai_results,
        output_dir,
    )

    plot_end_to_end_results(
        end_to_end_results,
        output_dir,
    )

    print("Plots generated successfully.")
    print(f"Saved to: {output_dir}")


if __name__ == "__main__":
    main()