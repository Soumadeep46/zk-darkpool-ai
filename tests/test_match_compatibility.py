import pytest

from src.crypto.commitments import poseidon_commit, random_nonce
from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier


@pytest.fixture(scope="module")
def prover():
    return SnarkProver("match_compatibility")


@pytest.fixture(scope="module")
def verifier():
    return SnarkVerifier("match_compatibility")


def create_match_inputs(
    buy_price: int = 1050,
    sell_price: int = 1000,
    buy_volume: int = 500,
    sell_volume: int = 500,
) -> dict:
    buy_price_nonce = random_nonce()
    sell_price_nonce = random_nonce()
    buy_volume_nonce = random_nonce()
    sell_volume_nonce = random_nonce()

    return {
        "buy_price": buy_price,
        "sell_price": sell_price,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "buy_price_nonce": buy_price_nonce,
        "sell_price_nonce": sell_price_nonce,
        "buy_volume_nonce": buy_volume_nonce,
        "sell_volume_nonce": sell_volume_nonce,
        "buy_price_commitment": poseidon_commit(
            buy_price,
            buy_price_nonce,
        ),
        "sell_price_commitment": poseidon_commit(
            sell_price,
            sell_price_nonce,
        ),
        "buy_volume_commitment": poseidon_commit(
            buy_volume,
            buy_volume_nonce,
        ),
        "sell_volume_commitment": poseidon_commit(
            sell_volume,
            sell_volume_nonce,
        ),
    }


def test_valid_match_proof(prover, verifier):
    inputs = create_match_inputs()

    proof_result = prover.prove(inputs)

    verification_result = verifier.verify(
        proof_result.proof,
        proof_result.public_signals,
    )

    assert proof_result.success is True
    assert verification_result["valid"] is True


def test_buy_price_below_sell_price_fails(prover):
    inputs = create_match_inputs(
        buy_price=999,
        sell_price=1000,
    )

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_different_volumes_fail(prover):
    inputs = create_match_inputs(
        buy_volume=500,
        sell_volume=1000,
    )

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_tampered_buy_price_commitment_fails(prover):
    inputs = create_match_inputs()

    inputs["buy_price_commitment"] = str(
        int(inputs["buy_price_commitment"]) + 1
    )

    with pytest.raises(Exception):
        prover.prove(inputs)


def test_tampered_sell_volume_commitment_fails(prover):
    inputs = create_match_inputs()

    inputs["sell_volume_commitment"] = str(
        int(inputs["sell_volume_commitment"]) + 1
    )

    with pytest.raises(Exception):
        prover.prove(inputs)