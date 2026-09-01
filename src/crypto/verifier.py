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
                "Could not find npx.\n"
                "Install Node.js and npm in the runtime environment."
            )

        if not self.verification_key.exists():
            raise FileNotFoundError(
                "Verification key not found.\n"
                f"Circuit: {circuit}\n"
                f"Expected path: {self.verification_key}"
            )

    def _snarkjs_command(self) -> list[str]:
        return [
            self.npx,
            "--yes",
            "--package=snarkjs@0.7.6",
            "snarkjs",
        ]

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

            proof_path.write_text(
                json.dumps(
                    proof,
                    indent=2,
                ),
                encoding="utf-8",
            )

            public_path.write_text(
                json.dumps(
                    public_signals,
                    indent=2,
                ),
                encoding="utf-8",
            )

            verification_start = time.perf_counter()

            verification_command = (
                self._snarkjs_command()
                + [
                    "groth16",
                    "verify",
                    str(self.verification_key),
                    str(public_path),
                    str(proof_path),
                ]
            )

            try:
                result = subprocess.run(
                    verification_command,
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

            valid = result.returncode == 0

            return {
                "valid": valid,
                "verification_time_ms": (
                    verification_time_ms
                ),
            }
