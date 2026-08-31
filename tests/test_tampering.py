import pytest

from src.crypto.commitments import poseidon_commit, random_nonce
from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier


@pytest.fixture(scope="module")
def prover():
    return SnarkProver("order_validity")


@pytest.fixture(scope="module")
def verifier():
    return SnarkVerifier("order_validity")


def create_inputs() -> dict:
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


def test_tampered_price_commitment_fails(prover):
    inputs = create_inputs()

    inputs["price_commitment"] = str(
        int(inputs["price_commitment"]) + 1
    )

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_tampered_volume_commitment_fails(prover):
    inputs = create_inputs()

    inputs["volume_commitment"] = str(
        int(inputs["volume_commitment"]) + 1
    )

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_wrong_price_nonce_fails(prover):
    inputs = create_inputs()

    inputs["price_nonce"] += 1

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_modified_public_signal_fails(prover, verifier):
    inputs = create_inputs()

    proof_result = prover.prove(inputs)

    tampered_signals = proof_result.public_signals.copy()
    tampered_signals[1] = str(
        int(tampered_signals[1]) + 1
    )

    result = verifier.verify(
        proof_result.proof,
        tampered_signals,
    )

    assert result["valid"] is False