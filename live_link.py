from uuid import uuid4
import time

import streamlit as st

from src.ai.candidate_router import CandidateRouter
from src.crypto.commitments import poseidon_commit, random_nonce
from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier
from src.exchange.candidate_generator import generate_candidates
from src.exchange.matching_engine import MatchingEngine
from src.exchange.private_order_book import PrivateOrderBook
from src.exchange.settlement import SettlementEngine
from src.models.order import PrivateOrder, PublicOrder


st.set_page_config(
    page_title="ZK-DarkPool AI",
    layout="wide",
)


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
):

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

    proof_result = prover.prove(
        proof_inputs
    )

    verification_result = verifier.verify(
        proof_result.proof,
        proof_result.public_signals,
    )

    proof_valid = verification_result.get(
        "valid",
        False,
    )

    if not proof_valid:

        raise ValueError(
            "Order proof verification failed "
            f"for order {order.order_id}"
        )

    public_order = PublicOrder(
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

    return (
        public_order,
        price_commitment,
        volume_commitment,
        proof_result,
        verification_result,
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


def get_volume_bucket(
    volume: int,
) -> int:

    if volume <= 100:
        return 1

    if volume <= 500:
        return 2

    if volume <= 1000:
        return 3

    return 4


def get_liquidity_bucket(
    volume: int,
) -> int:

    if volume <= 100:
        return 1

    if volume <= 500:
        return 2

    if volume <= 1000:
        return 3

    return 4


def shorten_value(
    value,
    length: int = 24,
) -> str:

    value = str(value)

    if len(value) <= length:
        return value

    return value[:length] + "..."


def display_public_order(
    title: str,
    order: PublicOrder,
):

    st.subheader(
        title
    )

    st.write(
        f"Order ID: `{order.order_id}`"
    )

    st.write(
        f"Side: `{order.side}`"
    )

    st.write(
        f"Asset: `{order.asset}`"
    )

    st.write(
        "Private Price: Hidden"
    )

    st.write(
        "Private Quantity: Hidden"
    )

    st.write(
        f"Price Commitment: "
        f"`{shorten_value(order.price_commitment)}`"
    )

    st.write(
        f"Volume Commitment: "
        f"`{shorten_value(order.volume_commitment)}`"
    )

    st.write(
        f"Volume Bucket: "
        f"`{order.coarse_volume_bucket}`"
    )

    st.write(
        f"Liquidity Bucket: "
        f"`{order.liquidity_bucket}`"
    )

    st.write(
        f"Volatility Regime: "
        f"`{order.volatility_regime}`"
    )

    st.write(
        f"Arrival Intensity: "
        f"`{order.arrival_intensity}`"
    )

    st.write(
        f"Order Proof Valid: "
        f"`{order.proof_valid}`"
    )


def main():

    st.title(
        "ZK-DarkPool AI"
    )

    st.write(
        "Interactive Private Order Matching and "
        "Zero-Knowledge Verification Demonstration"
    )

    st.divider()

    st.header(
        "Private Order Input"
    )

    left_column, right_column = st.columns(
        2
    )

    with left_column:

        st.subheader(
            "Buyer Order"
        )

        buyer_price = st.number_input(
            "Buyer Maximum Price",
            min_value=1,
            value=1050,
            step=1,
        )

        buyer_quantity = st.number_input(
            "Buyer Quantity",
            min_value=1,
            value=500,
            step=1,
        )

    with right_column:

        st.subheader(
            "Seller Order"
        )

        seller_price = st.number_input(
            "Seller Minimum Price",
            min_value=1,
            value=1000,
            step=1,
        )

        seller_quantity = st.number_input(
            "Seller Quantity",
            min_value=1,
            value=500,
            step=1,
        )

    st.divider()

    execute = st.button(
        "Execute Private Match",
        use_container_width=True,
    )

    if not execute:

        st.info(
            "Enter buyer and seller order values, "
            "then execute the private matching pipeline."
        )

        return

    st.header(
        "Execution Pipeline"
    )

    progress_bar = st.progress(
        0
    )

    status = st.empty()

    try:

        status.write(
            "Step 1 of 7: Creating private orders"
        )

        st.subheader(
            "Step 1: Private Order Creation"
        )

        buy_private = create_private_order(
            side="BUY",
            price=int(buyer_price),
            volume=int(buyer_quantity),
        )

        sell_private = create_private_order(
            side="SELL",
            price=int(seller_price),
            volume=int(seller_quantity),
        )

        st.write(
            "Two private orders were created."
        )

        st.write(
            "The price and quantity values remain "
            "inside the private order objects."
        )

        st.write(
            f"Buyer Order ID: `{buy_private.order_id}`"
        )

        st.write(
            f"Seller Order ID: `{sell_private.order_id}`"
        )

        progress_bar.progress(
            10
        )

        time.sleep(
            0.2
        )

        status.write(
            "Step 2 of 7: Initializing zero-knowledge provers"
        )

        st.subheader(
            "Step 2: Zero-Knowledge Proof Initialization"
        )

        order_prover = SnarkProver(
            "order_validity"
        )

        order_verifier = SnarkVerifier(
            "order_validity"
        )

        st.write(
            "The order validity proving and verification "
            "components were initialized."
        )

        st.write(
            "The circuit validates committed private "
            "price and volume constraints."
        )

        progress_bar.progress(
            20
        )

        time.sleep(
            0.2
        )

        status.write(
            "Step 3 of 7: Generating Poseidon commitments"
        )

        st.subheader(
            "Step 3: Private Order Commitment"
        )

        buyer_volume_bucket = get_volume_bucket(
            int(buyer_quantity)
        )

        seller_volume_bucket = get_volume_bucket(
            int(seller_quantity)
        )

        buyer_liquidity_bucket = get_liquidity_bucket(
            int(buyer_quantity)
        )

        seller_liquidity_bucket = get_liquidity_bucket(
            int(seller_quantity)
        )

        (
            buy_public,
            buy_price_commitment,
            buy_volume_commitment,
            buy_proof,
            buy_verification,
        ) = create_public_order(
            order=buy_private,
            prover=order_prover,
            verifier=order_verifier,
            volume_bucket=buyer_volume_bucket,
            liquidity_bucket=buyer_liquidity_bucket,
            volatility_regime=1,
            arrival_intensity=0.72,
        )

        (
            sell_public,
            sell_price_commitment,
            sell_volume_commitment,
            sell_proof,
            sell_verification,
        ) = create_public_order(
            order=sell_private,
            prover=order_prover,
            verifier=order_verifier,
            volume_bucket=seller_volume_bucket,
            liquidity_bucket=seller_liquidity_bucket,
            volatility_regime=1,
            arrival_intensity=0.68,
        )

        commitment_column_1, commitment_column_2 = (
            st.columns(
                2
            )
        )

        with commitment_column_1:

            st.write(
                "Buyer Commitments"
            )

            st.write(
                "Price Commitment"
            )

            st.code(
                str(
                    buy_price_commitment
                )
            )

            st.write(
                "Volume Commitment"
            )

            st.code(
                str(
                    buy_volume_commitment
                )
            )

        with commitment_column_2:

            st.write(
                "Seller Commitments"
            )

            st.write(
                "Price Commitment"
            )

            st.code(
                str(
                    sell_price_commitment
                )
            )

            st.write(
                "Volume Commitment"
            )

            st.code(
                str(
                    sell_volume_commitment
                )
            )

        st.write(
            "Each private value was combined with a "
            "cryptographic nonce and converted into a "
            "Poseidon commitment."
        )

        progress_bar.progress(
            35
        )

        time.sleep(
            0.2
        )

        status.write(
            "Step 4 of 7: Verifying private order validity"
        )

        st.subheader(
            "Step 4: Zero-Knowledge Order Validation"
        )

        validation_column_1, validation_column_2 = (
            st.columns(
                2
            )
        )

        with validation_column_1:

            st.write(
                "Buyer Order"
            )

            st.write(
                "Price Commitment Constraint: Valid"
            )

            st.write(
                "Volume Commitment Constraint: Valid"
            )

            st.write(
                "Zero-Knowledge Proof Generated: Valid"
            )

            st.write(
                "Proof Verification: "
                f"{buy_verification.get('valid', False)}"
            )

        with validation_column_2:

            st.write(
                "Seller Order"
            )

            st.write(
                "Price Commitment Constraint: Valid"
            )

            st.write(
                "Volume Commitment Constraint: Valid"
            )

            st.write(
                "Zero-Knowledge Proof Generated: Valid"
            )

            st.write(
                "Proof Verification: "
                f"{sell_verification.get('valid', False)}"
            )

        progress_bar.progress(
            50
        )

        time.sleep(
            0.2
        )

        status.write(
            "Step 5 of 7: Building public order book "
            "and generating candidates"
        )

        st.subheader(
            "Step 5: Public Order Book and AI Candidate Routing"
        )

        order_book = PrivateOrderBook()

        order_book.add(
            buy_public
        )

        order_book.add(
            sell_public
        )

        candidates = generate_candidates(
            order_book.all()
        )

        router = CandidateRouter()

        selected_candidates = router.select(
            candidates
        )

        st.write(
            f"Public Orders: `{len(order_book)}`"
        )

        st.write(
            f"Generated Candidate Pairs: "
            f"`{len(candidates)}`"
        )

        st.write(
            f"Candidates Selected by AI: "
            f"`{len(selected_candidates)}`"
        )

        st.write(
            f"Candidates Eliminated by AI: "
            f"`{len(candidates) - len(selected_candidates)}`"
        )

        progress_bar.progress(
            65
        )

        time.sleep(
            0.2
        )

        status.write(
            "Step 6 of 7: Running private match verification"
        )

        st.subheader(
            "Step 6: Zero-Knowledge Match Verification"
        )

        private_orders = {
            buy_private.order_id: buy_private,
            sell_private.order_id: sell_private,
        }

        proof_inputs = {}

        for candidate in selected_candidates:

            candidate_buy_order = (
                private_orders[
                    candidate.buy_order_id
                ]
            )

            candidate_sell_order = (
                private_orders[
                    candidate.sell_order_id
                ]
            )

            proof_inputs[
                (
                    candidate.buy_order_id,
                    candidate.sell_order_id,
                )
            ] = build_match_inputs(
                candidate_buy_order,
                candidate_sell_order,
            )

        matching_engine = MatchingEngine()

        match_results = matching_engine.match(
            selected_candidates,
            proof_inputs,
        )

        if not selected_candidates:

            st.warning(
                "No candidate was selected for "
                "private match verification."
            )

        else:

            st.write(
                "The selected candidate pairs were passed "
                "to the match compatibility verification stage."
            )

        valid_match_count = sum(
            1
            for result in match_results
            if result.valid
        )

        st.write(
            f"Match Proofs Executed: "
            f"`{len(match_results)}`"
        )

        st.write(
            f"Valid Matches: "
            f"`{valid_match_count}`"
        )

        progress_bar.progress(
            80
        )

        time.sleep(
            0.2
        )

        status.write(
            "Step 7 of 7: Processing settlement"
        )

        st.subheader(
            "Step 7: Settlement"
        )

        settlement_engine = SettlementEngine()

        settlements = []

        for result in match_results:

            if result.valid:

                buy_order = private_orders[
                    result.buy_order_id
                ]

                sell_order = private_orders[
                    result.sell_order_id
                ]

                settlement = (
                    settlement_engine.settle(
                        match=result,
                        buy_quantity=buy_order.private_volume,
                        sell_quantity=sell_order.private_volume,
                    )
                )

                settlements.append(
                    settlement
                )

        if settlements:

            st.success(
                "Private match verification succeeded "
                "and settlement was completed."
            )

            for settlement in settlements:

                st.write(
                    f"Settlement ID: "
                    f"`{settlement.settlement_id}`"
                )

                st.write(
                    f"Executed Quantity: "
                    f"`{settlement.executed_quantity}`"
                )

                st.write(
                    f"Buyer Remaining Quantity: "
                    f"`{settlement.buyer_remaining_quantity}`"
                )

                st.write(
                    f"Seller Remaining Quantity: "
                    f"`{settlement.seller_remaining_quantity}`"
                )

                st.write(
                    f"Buyer Status: "
                    f"`{settlement.buyer_status}`"
                )

                st.write(
                    f"Seller Status: "
                    f"`{settlement.seller_status}`"
                )

                st.write(
                    f"Settlement Status: "
                    f"`{settlement.status}`"
                )

                st.divider()

        else:

            st.error(
                "No compatible private order match "
                "was settled."
            )

            if int(buyer_price) < int(seller_price):

                st.write(
                    "Compatibility condition failed: "
                    "buyer price is lower than seller price."
                )

        progress_bar.progress(
            100
        )

        status.write(
            "Private matching pipeline completed"
        )

        st.divider()

        st.header(
            "Public View"
        )

        st.write(
            "This section represents information that can "
            "be exposed without revealing private prices, "
            "quantities, or cryptographic nonces."
        )

        public_column_1, public_column_2 = (
            st.columns(
                2
            )
        )

        with public_column_1:

            display_public_order(
                "Buyer Public Order",
                buy_public,
            )

        with public_column_2:

            display_public_order(
                "Seller Public Order",
                sell_public,
            )

        st.divider()

        st.header(
            "Execution Summary"
        )

        summary_column_1, summary_column_2, summary_column_3 = (
            st.columns(
                3
            )
        )

        with summary_column_1:

            st.metric(
                "Private Orders",
                2,
            )

            st.metric(
                "Commitments Generated",
                4,
            )

        with summary_column_2:

            st.metric(
                "Candidate Pairs",
                len(candidates),
            )

            st.metric(
                "AI Selected",
                len(selected_candidates),
            )

        with summary_column_3:

            st.metric(
                "Valid Matches",
                valid_match_count,
            )

            st.metric(
                "Settlements",
                len(settlements),
            )

        st.divider()

        st.header(
            "Private Execution View"
        )

        st.write(
            "This section exposes the underlying witness "
            "data for demonstration and debugging purposes."
        )

        with st.expander(
            "View Buyer Private Data"
        ):

            st.write(
                f"Order ID: "
                f"`{buy_private.order_id}`"
            )

            st.write(
                f"Side: "
                f"`{buy_private.side}`"
            )

            st.write(
                f"Private Price: "
                f"`{buy_private.private_price}`"
            )

            st.write(
                f"Private Quantity: "
                f"`{buy_private.private_volume}`"
            )

            st.write(
                "Price Nonce"
            )

            st.code(
                str(
                    buy_private.price_nonce
                )
            )

            st.write(
                "Volume Nonce"
            )

            st.code(
                str(
                    buy_private.volume_nonce
                )
            )

            st.write(
                "Price Commitment"
            )

            st.code(
                str(
                    buy_price_commitment
                )
            )

            st.write(
                "Volume Commitment"
            )

            st.code(
                str(
                    buy_volume_commitment
                )
            )

        with st.expander(
            "View Seller Private Data"
        ):

            st.write(
                f"Order ID: "
                f"`{sell_private.order_id}`"
            )

            st.write(
                f"Side: "
                f"`{sell_private.side}`"
            )

            st.write(
                f"Private Price: "
                f"`{sell_private.private_price}`"
            )

            st.write(
                f"Private Quantity: "
                f"`{sell_private.private_volume}`"
            )

            st.write(
                "Price Nonce"
            )

            st.code(
                str(
                    sell_private.price_nonce
                )
            )

            st.write(
                "Volume Nonce"
            )

            st.code(
                str(
                    sell_private.volume_nonce
                )
            )

            st.write(
                "Price Commitment"
            )

            st.code(
                str(
                    sell_price_commitment
                )
            )

            st.write(
                "Volume Commitment"
            )

            st.code(
                str(
                    sell_volume_commitment
                )
            )

        with st.expander(
            "View Private Match Inputs"
        ):

            st.write(
                "Buyer Private Price"
            )

            st.code(
                str(
                    buy_private.private_price
                )
            )

            st.write(
                "Seller Private Price"
            )

            st.code(
                str(
                    sell_private.private_price
                )
            )

            st.write(
                "Buyer Private Quantity"
            )

            st.code(
                str(
                    buy_private.private_volume
                )
            )

            st.write(
                "Seller Private Quantity"
            )

            st.code(
                str(
                    sell_private.private_volume
                )
            )

            st.write(
                "Price Compatibility Condition"
            )

            st.code(
                "buy_price >= sell_price"
            )

            st.write(
                "Quantity Execution Rule"
            )

            st.code(
                "executed_quantity = min(buy_volume, sell_volume)"
            )

            st.write(
                "Buyer Remaining Quantity Rule"
            )

            st.code(
                "buyer_remaining = buy_volume - executed_quantity"
            )

            st.write(
                "Seller Remaining Quantity Rule"
            )

            st.code(
                "seller_remaining = sell_volume - executed_quantity"
            )

            executed_quantity = min(
                buy_private.private_volume,
                sell_private.private_volume,
            )

            buyer_remaining = (
                buy_private.private_volume
                - executed_quantity
            )

            seller_remaining = (
                sell_private.private_volume
                - executed_quantity
            )

            st.write(
                "Calculated Execution Quantity"
            )

            st.code(
                str(
                    executed_quantity
                )
            )

            st.write(
                "Calculated Buyer Remaining Quantity"
            )

            st.code(
                str(
                    buyer_remaining
                )
            )

            st.write(
                "Calculated Seller Remaining Quantity"
            )

            st.code(
                str(
                    seller_remaining
                )
            )

        with st.expander(
            "View Match Results"
        ):

            if match_results:

                for result in match_results:

                    st.write(
                        f"Buyer Order ID: "
                        f"`{result.buy_order_id}`"
                    )

                    st.write(
                        f"Seller Order ID: "
                        f"`{result.sell_order_id}`"
                    )

                    st.write(
                        f"Proof Valid: "
                        f"`{result.valid}`"
                    )

                    st.write(
                        "Verification Time: "
                        f"`{result.verification_time_ms:.2f} ms`"
                    )

                    st.divider()

            else:

                st.write(
                    "No match result was generated."
                )

        with st.expander(
            "View Settlement Results"
        ):

            if settlements:

                for settlement in settlements:

                    st.write(
                        f"Executed Quantity: "
                        f"`{settlement.executed_quantity}`"
                    )

                    st.write(
                        f"Buyer Remaining Quantity: "
                        f"`{settlement.buyer_remaining_quantity}`"
                    )

                    st.write(
                        f"Seller Remaining Quantity: "
                        f"`{settlement.seller_remaining_quantity}`"
                    )

                    st.write(
                        f"Buyer Execution Status: "
                        f"`{settlement.buyer_status}`"
                    )

                    st.write(
                        f"Seller Execution Status: "
                        f"`{settlement.seller_status}`"
                    )

                    st.write(
                        f"Settlement Status: "
                        f"`{settlement.status}`"
                    )

                    st.divider()

            else:

                st.write(
                    "No settlement record was created."
                )

    except Exception as error:

        progress_bar.empty()

        status.empty()

        st.error(
            "The execution pipeline encountered an error."
        )

        st.exception(
            error
        )


if __name__ == "__main__":
    main()