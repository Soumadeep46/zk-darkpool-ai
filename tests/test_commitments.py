import pytest

from src.crypto.commitments import poseidon_commit


def test_commitment_is_deterministic():
    commitment_1 = poseidon_commit(1000, 12345)
    commitment_2 = poseidon_commit(1000, 12345)

    assert commitment_1 == commitment_2


def test_different_nonce_changes_commitment():
    commitment_1 = poseidon_commit(1000, 12345)
    commitment_2 = poseidon_commit(1000, 54321)

    assert commitment_1 != commitment_2


def test_different_value_changes_commitment():
    commitment_1 = poseidon_commit(1000, 12345)
    commitment_2 = poseidon_commit(1001, 12345)

    assert commitment_1 != commitment_2


def test_negative_value_raises_error():
    with pytest.raises(ValueError):
        poseidon_commit(-1, 12345)


def test_negative_nonce_raises_error():
    with pytest.raises(ValueError):
        poseidon_commit(1000, -1)