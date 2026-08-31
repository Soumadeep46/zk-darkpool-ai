from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import time


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass
class VerificationResult:
    valid: bool
    verification_time_ms: float


class SnarkVerifier:
    def __init__(self, circuit: str):
        self.circuit = circuit

        self.verification_key = (
            ROOT_DIR
            / "artifacts"
            / f"{circuit}_verification_key.json"
        )

        self.npx = (
            shutil.which("npx.cmd")
            or shutil.which("npx")
        )

        if self.npx is None:
            raise FileNotFoundError(
                "Could not find npx. "
                "Make sure Node.js is installed and "
                "npx is available in PATH."
            )

        if not self.verification_key.exists():
            raise FileNotFoundError(
                "Verification key not found.\n"
                f"Circuit: {circuit}\n"
                f"Expected path: {self.verification_key}"
            )

    def verify(
        self,
        proof: dict,
        public_signals: list[str],
    ) -> dict:

        with TemporaryDirectory(
            prefix="zk-darkpool-verify-"
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            proof_path = (
                temp_dir / "proof.json"
            )

            public_path = (
                temp_dir / "public.json"
            )

            # Save proof.
            proof_path.write_text(
                json.dumps(
                    proof,
                    indent=2,
                ),
                encoding="utf-8",
            )

            # Save public signals.
            public_path.write_text(
                json.dumps(
                    public_signals,
                    indent=2,
                ),
                encoding="utf-8",
            )

            verification_start = time.perf_counter()

            try:
                result = subprocess.run(
                    [
                        self.npx,
                        "snarkjs",
                        "groth16",
                        "verify",
                        str(self.verification_key),
                        str(public_path),
                        str(proof_path),
                    ],
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                )

            except FileNotFoundError as error:
                raise RuntimeError(
                    "Could not execute npx.\n"
                    f"Resolved npx path: {self.npx}"
                ) from error

            verification_end = time.perf_counter()

            verification_time_ms = (
                verification_end
                - verification_start
            ) * 1000

            # snarkjs returns exit code 0 for a valid proof.
            valid = result.returncode == 0

            return {
                "valid": valid,
                "verification_time_ms": (
                    verification_time_ms
                ),
            }