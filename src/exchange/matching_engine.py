from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, local, get_ident
from time import perf_counter
import os

from src.crypto.prover import SnarkProver
from src.crypto.verifier import SnarkVerifier
from src.models.match import CandidatePair, MatchResult


class MatchingEngine:

    def __init__(
        self,
        max_workers: int | None = None,
    ):
        cpu_count = (
            os.cpu_count()
            or 4
        )

        self.max_workers = (
            max_workers
            or min(8, cpu_count)
        )

        self._thread_local = local()

        self._active_lock = Lock()
        self._active_tasks = 0
        self._max_active_tasks = 0

    def _get_prover(self) -> SnarkProver:

        if not hasattr(
            self._thread_local,
            "prover",
        ):
            self._thread_local.prover = (
                SnarkProver(
                    "match_compatibility"
                )
            )

        return self._thread_local.prover

    def _get_verifier(self) -> SnarkVerifier:

        if not hasattr(
            self._thread_local,
            "verifier",
        ):
            self._thread_local.verifier = (
                SnarkVerifier(
                    "match_compatibility"
                )
            )

        return self._thread_local.verifier

    def verify_candidate(
        self,
        candidate: CandidatePair,
        match_inputs: dict,
    ) -> MatchResult:

        thread_id = get_ident()

        with self._active_lock:

            self._active_tasks += 1

            self._max_active_tasks = max(
                self._max_active_tasks,
                self._active_tasks,
            )

            active_count = (
                self._active_tasks
            )

        start = perf_counter()

        print(
            f"[START] "
            f"Thread={thread_id} "
            f"Active={active_count} "
            f"Buy={candidate.buy_order_id[:8]} "
            f"Sell={candidate.sell_order_id[:8]}",
            flush=True,
        )

        try:

            prover = self._get_prover()

            verifier = self._get_verifier()

            proof_result = prover.prove(
                match_inputs
            )

            verification_result = (
                verifier.verify(
                    proof_result.proof,
                    proof_result.public_signals,
                )
            )

            return MatchResult(
                buy_order_id=(
                    candidate.buy_order_id
                ),
                sell_order_id=(
                    candidate.sell_order_id
                ),
                valid=verification_result[
                    "valid"
                ],
                verification_time_ms=(
                    verification_result[
                        "verification_time_ms"
                    ]
                ),
            )

        finally:

            elapsed = (
                perf_counter() - start
            )

            with self._active_lock:

                self._active_tasks -= 1

                active_count = (
                    self._active_tasks
                )

            print(
                f"[END] "
                f"Thread={thread_id} "
                f"Active={active_count} "
                f"Elapsed={elapsed:.2f}s",
                flush=True,
            )

    def _verify_candidate_safe(
        self,
        candidate: CandidatePair,
        match_inputs: dict,
    ) -> MatchResult:

        try:

            return self.verify_candidate(
                candidate,
                match_inputs,
            )

        except Exception as error:

            print(
                f"Match verification failed for "
                f"({candidate.buy_order_id}, "
                f"{candidate.sell_order_id}): "
                f"{error}",
                flush=True,
            )

            return MatchResult(
                buy_order_id=(
                    candidate.buy_order_id
                ),
                sell_order_id=(
                    candidate.sell_order_id
                ),
                valid=False,
                verification_time_ms=0.0,
            )

    def match(
        self,
        candidates: list[CandidatePair],
        proof_inputs: dict[
            tuple[str, str],
            dict,
        ],
    ) -> list[MatchResult]:

        tasks = []

        for candidate in candidates:

            key = (
                candidate.buy_order_id,
                candidate.sell_order_id,
            )

            if key not in proof_inputs:
                continue

            tasks.append(
                (
                    candidate,
                    proof_inputs[key],
                )
            )

        if not tasks:
            return []

        results = []

        worker_count = min(
            self.max_workers,
            len(tasks),
        )

        print(
            f"\nZK Matching: "
            f"{len(tasks)} candidates | "
            f"{worker_count} parallel workers\n",
            flush=True,
        )

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:

            future_map = {}

            for (
                candidate,
                match_inputs,
            ) in tasks:

                future = executor.submit(
                    self._verify_candidate_safe,
                    candidate,
                    match_inputs,
                )

                future_map[
                    future
                ] = candidate

            for future in as_completed(
                future_map
            ):

                result = future.result()

                results.append(
                    result
                )

        print(
            f"\nMaximum simultaneous ZK tasks: "
            f"{self._max_active_tasks}/"
            f"{worker_count}\n",
            flush=True,
        )

        return results