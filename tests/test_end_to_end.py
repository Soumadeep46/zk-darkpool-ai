from uuid import uuid4

from src.crypto.commitments import poseidon_commit, random_nonce
from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier
from src.exchange.candidate_generator import generate_candidates
from src.exchange.matching_engine import MatchingEngine
from src.exchange.private_order_book import PrivateOrderBook
from src.exchange.settlement import SettlementEngine
from src.models.order import PrivateOrder, PublicOrder


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

    assert verification_result["valid"] is True

    return PublicOrder(
        order_id=order.order_id,
        side=order.side,
        asset=order.asset,
        coarse_volume_bucket=volume_bucket,
        liquidity_bucket=2,
        volatility_regime=1,
        arrival_intensity=0.5,
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


def test_complete_valid_trade():
    order_prover = SnarkProver("order_validity")
    order_verifier = SnarkVerifier("order_validity")

    buy_private = create_private_order(
        side="BUY",
        price=1050,
        volume=500,
    )

    sell_private = create_private_order(
        side="SELL",
        price=1000,
        volume=500,
    )

    buy_public = create_public_order(
        buy_private,
        order_prover,
        order_verifier,
        volume_bucket=2,
    )

    sell_public = create_public_order(
        sell_private,
        order_prover,
        order_verifier,
        volume_bucket=2,
    )

    order_book = PrivateOrderBook()
    order_book.add(buy_public)
    order_book.add(sell_public)

    candidates = generate_candidates(
        order_book.all()
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    matching_engine = MatchingEngine()

    proof_inputs = {
        (
            candidate.buy_order_id,
            candidate.sell_order_id,
        ): build_match_inputs(
            buy_private,
            sell_private,
        )
    }

    results = matching_engine.match(
        [candidate],
        proof_inputs,
    )

    assert len(results) == 1
    assert results[0].valid is True

    settlement_engine = SettlementEngine()

    settlement = settlement_engine.settle(
        results[0]
    )

    assert settlement.status == "SETTLED"
    assert len(settlement_engine) == 1


def test_invalid_trade_is_not_settled():
    buy_private = create_private_order(
        side="BUY",
        price=900,
        volume=500,
    )

    sell_private = create_private_order(
        side="SELL",
        price=1000,
        volume=500,
    )

    matching_engine = MatchingEngine()

    from src.models.match import CandidatePair

    candidate = CandidatePair(
        buy_order_id=buy_private.order_id,
        sell_order_id=sell_private.order_id,
        features={},
    )

    proof_inputs = {
        (
            candidate.buy_order_id,
            candidate.sell_order_id,
        ): build_match_inputs(
            buy_private,
            sell_private,
        )
    }

    results = matching_engine.match(
        [candidate],
        proof_inputs,
    )

    assert len(results) == 1
    assert results[0].valid is False