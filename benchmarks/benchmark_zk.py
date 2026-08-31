import json
from pathlib import Path

from src.crypto.commitments import poseidon_commit, random_nonce
from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier
from src.utils.config import load_config
from src.utils.metrics import summarize


ROOT_DIR = Path(__file__).resolve().parents[1]


def create_order_inputs() -> dict:
    price = 1000
    volume = 500

    price_nonce = random_nonce()
    volume_nonce = random_nonce()

    return {
        "price": price,
        "volume": volume,
        "price_nonce": price_nonce,
        "volume_nonce": volume_nonce,
        "price_commitment": poseidon_commit(
            price,
            price_nonce,
        ),
        "volume_commitment": poseidon_commit(
            volume,
            volume_nonce,
        ),
    }


def benchmark_order_validity() -> dict:
    config = load_config()

    repetitions = config["benchmark"]["repetitions"]
    warmup_iterations = config["benchmark"]["warmup_iterations"]

    prover = SnarkProver("order_validity")
    verifier = SnarkVerifier("order_validity")

    for _ in range(warmup_iterations):
        inputs = create_order_inputs()
        proof_result = prover.prove(inputs)

        verifier.verify(
            proof_result.proof,
            proof_result.public_signals,
        )

    witness_times = []
    proof_times = []
    verification_times = []

    for _ in range(repetitions):
        inputs = create_order_inputs()

        proof_result = prover.prove(inputs)

        verification_result = verifier.verify(
            proof_result.proof,
            proof_result.public_signals,
        )

        if not verification_result["valid"]:
            raise RuntimeError(
                "Generated proof failed verification"
            )

        witness_times.append(
            proof_result.witness_time_ms
        )

        proof_times.append(
            proof_result.proof_time_ms
        )

        verification_times.append(
            verification_result["verification_time_ms"]
        )

    return {
        "circuit": "order_validity",
        "repetitions": repetitions,
        "witness_generation": summarize(
            witness_times
        ),
        "proof_generation": summarize(
            proof_times
        ),
        "verification": summarize(
            verification_times
        ),
    }


def save_results(results: dict) -> Path:
    config = load_config()

    output_path = (
        ROOT_DIR
        / config["paths"]["results_metrics"]
        / "zk_benchmark.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    return output_path


def main():
    results = benchmark_order_validity()
    output_path = save_results(results)

    print("ZK Benchmark Results")

    for category, metrics in results.items():
        if not isinstance(metrics, dict):
            continue

        print(f"\n{category}")

        for name, value in metrics.items():
            print(f"{name}: {value:.3f}")

    print(f"\nSaved results to: {output_path}")


if __name__ == "__main__":
    main()