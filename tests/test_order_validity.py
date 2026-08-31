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


def create_valid_inputs(
    price: int = 1000,
    volume: int = 500,
) -> dict:
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


def test_valid_order_proof(prover, verifier):
    inputs = create_valid_inputs()

    proof_result = prover.prove(inputs)

    verification_result = verifier.verify(
        proof_result.proof,
        proof_result.public_signals,
    )

    assert proof_result.success is True
    assert verification_result["valid"] is True


def test_price_below_minimum_fails(prover):
    inputs = create_valid_inputs(price=0)

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_price_above_maximum_fails(prover):
    inputs = create_valid_inputs(price=1_000_001)

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_volume_below_minimum_fails(prover):
    inputs = create_valid_inputs(volume=0)

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_volume_above_maximum_fails(prover):
    inputs = create_valid_inputs(volume=1_000_001)

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_tampered_public_signal_fails(prover, verifier):
    inputs = create_valid_inputs()

    proof_result = prover.prove(inputs)

    tampered_signals = proof_result.public_signals.copy()
    tampered_signals[0] = str(
        int(tampered_signals[0]) + 1
    )

    verification_result = verifier.verify(
        proof_result.proof,
        tampered_signals,
    )

    assert verification_result["valid"] is False