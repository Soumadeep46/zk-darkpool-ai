from uuid import uuid4

from src.ai.candidate_router import CandidateRouter
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

    proof_inputs = {
        "price": order.private_price,
        "volume": order.private_volume,
        "price_nonce": order.price_nonce,
        "volume_nonce": order.volume_nonce,
        "price_commitment": price_commitment,
        "volume_commitment": volume_commitment,
    }

    proof_result = prover.prove(proof_inputs)

    verification_result = verifier.verify(
        proof_result.proof,
        proof_result.public_signals,
    )

    if not verification_result["valid"]:
        raise ValueError(
            f"Order proof verification failed: {order.order_id}"
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


def main():
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
        order=buy_private,
        prover=order_prover,
        verifier=order_verifier,
        volume_bucket=2,
        liquidity_bucket=3,
        volatility_regime=1,
        arrival_intensity=0.72,
    )

    sell_public = create_public_order(
        order=sell_private,
        prover=order_prover,
        verifier=order_verifier,
        volume_bucket=2,
        liquidity_bucket=2,
        volatility_regime=1,
        arrival_intensity=0.68,
    )

    order_book = PrivateOrderBook()
    order_book.add(buy_public)
    order_book.add(sell_public)

    candidates = generate_candidates(order_book.all())

    router = CandidateRouter()
    selected_candidates = router.select(candidates)

    private_orders = {
        buy_private.order_id: buy_private,
        sell_private.order_id: sell_private,
    }

    proof_inputs = {}

    for candidate in selected_candidates:
        buy_order = private_orders[candidate.buy_order_id]
        sell_order = private_orders[candidate.sell_order_id]

        proof_inputs[
            (
                candidate.buy_order_id,
                candidate.sell_order_id,
            )
        ] = build_match_inputs(
            buy_order,
            sell_order,
        )

    matching_engine = MatchingEngine()

    match_results = matching_engine.match(
        selected_candidates,
        proof_inputs,
    )

    settlement_engine = SettlementEngine()

    print("\nZK-DarkPool AI Demo")
    print(f"Public orders: {len(order_book)}")
    print(f"Generated candidates: {len(candidates)}")
    print(f"Selected candidates: {len(selected_candidates)}")

    for result in match_results:
        print(
            f"\nMatch: {result.buy_order_id} -> "
            f"{result.sell_order_id}"
        )
        print(f"Valid: {result.valid}")
        print(
            f"Verification time: "
            f"{result.verification_time_ms:.2f} ms"
        )

        if result.valid:
            settlement = settlement_engine.settle(result)

            print(
                f"Settlement: {settlement.settlement_id}"
            )
            print(f"Status: {settlement.status}")


if __name__ == "__main__":
    main()