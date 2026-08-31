from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import time


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass
class ProofResult:
    success: bool
    proof: dict
    public_signals: list[str]
    witness_time_ms: float
    proof_time_ms: float


class SnarkProver:
    def __init__(self, circuit: str):
        self.circuit = circuit

        # ==========================================
        # Circuit WASM
        # ==========================================

        self.wasm = (
            ROOT_DIR
            / "build"
            / circuit
            / f"{circuit}_js"
            / f"{circuit}.wasm"
        )

        # ==========================================
        # Groth16 proving key
        # ==========================================

        self.zkey = (
            ROOT_DIR
            / "artifacts"
            / f"{circuit}_final.zkey"
        )

        # ==========================================
        # Locate npx
        #
        # On Windows, executables are often exposed
        # as .cmd files, so explicitly check npx.cmd.
        # ==========================================

        self.npx = (
            shutil.which("npx.cmd")
            or shutil.which("npx")
        )

        if self.npx is None:
            raise FileNotFoundError(
                "Could not find npx.\n"
                "Make sure Node.js is installed and "
                "restart VS Code / PowerShell so PATH "
                "is refreshed."
            )

        # ==========================================
        # Validate required circuit artifacts
        # ==========================================

        if not self.wasm.exists():
            raise FileNotFoundError(
                "WASM file not found.\n"
                f"Circuit: {circuit}\n"
                f"Expected path: {self.wasm}"
            )

        if not self.zkey.exists():
            raise FileNotFoundError(
                "Proving key not found.\n"
                f"Circuit: {circuit}\n"
                f"Expected path: {self.zkey}"
            )

    def prove(
        self,
        inputs: dict,
    ) -> ProofResult:

        with TemporaryDirectory(
            prefix="zk-darkpool-"
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            input_path = (
                temp_dir / "input.json"
            )

            witness_path = (
                temp_dir / "witness.wtns"
            )

            proof_path = (
                temp_dir / "proof.json"
            )

            public_path = (
                temp_dir / "public.json"
            )

            # ==========================================
            # Circom field elements should be represented
            # as strings in JSON.
            # ==========================================

            input_data = {
                key: str(value)
                for key, value in inputs.items()
            }

            input_path.write_text(
                json.dumps(
                    input_data,
                    indent=2,
                ),
                encoding="utf-8",
            )

            # ==========================================
            # 1. Generate witness
            #
            # Equivalent PowerShell command:
            #
            # npx snarkjs wtns calculate \
            #     circuit.wasm input.json witness.wtns
            # ==========================================

            witness_start = time.perf_counter()

            try:
                subprocess.run(
                    [
                        self.npx,
                        "snarkjs",
                        "wtns",
                        "calculate",
                        str(self.wasm),
                        str(input_path),
                        str(witness_path),
                    ],
                    cwd=str(ROOT_DIR),
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except FileNotFoundError as error:
                raise RuntimeError(
                    "Could not execute npx.\n"
                    f"Resolved npx path: {self.npx}\n"
                    "Check your Node.js installation "
                    "and restart the terminal."
                ) from error

            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "Witness generation failed.\n\n"
                    f"Circuit: {self.circuit}\n\n"
                    f"Command:\n"
                    f"{self.npx} snarkjs wtns calculate "
                    f"{self.wasm} "
                    f"{input_path} "
                    f"{witness_path}\n\n"
                    f"Input:\n"
                    f"{json.dumps(input_data, indent=2)}\n\n"
                    f"STDOUT:\n"
                    f"{error.stdout}\n\n"
                    f"STDERR:\n"
                    f"{error.stderr}"
                ) from error

            witness_end = time.perf_counter()

            # Ensure witness was actually created.

            if not witness_path.exists():
                raise RuntimeError(
                    "Witness generation command completed "
                    "but witness.wtns was not created.\n"
                    f"Expected path: {witness_path}"
                )

            # ==========================================
            # 2. Generate Groth16 proof
            #
            # Equivalent PowerShell command:
            #
            # npx snarkjs groth16 prove \
            #     circuit_final.zkey \
            #     witness.wtns \
            #     proof.json \
            #     public.json
            # ==========================================

            proof_start = time.perf_counter()

            try:
                subprocess.run(
                    [
                        self.npx,
                        "snarkjs",
                        "groth16",
                        "prove",
                        str(self.zkey),
                        str(witness_path),
                        str(proof_path),
                        str(public_path),
                    ],
                    cwd=str(ROOT_DIR),
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except FileNotFoundError as error:
                raise RuntimeError(
                    "Could not execute npx while "
                    "generating the proof.\n"
                    f"Resolved npx path: {self.npx}"
                ) from error

            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "Proof generation failed.\n\n"
                    f"Circuit: {self.circuit}\n\n"
                    f"ZKey:\n{self.zkey}\n\n"
                    f"Witness:\n{witness_path}\n\n"
                    f"STDOUT:\n"
                    f"{error.stdout}\n\n"
                    f"STDERR:\n"
                    f"{error.stderr}"
                ) from error

            proof_end = time.perf_counter()

            # ==========================================
            # Validate proof artifacts
            # ==========================================

            if not proof_path.exists():
                raise RuntimeError(
                    "Proof generation completed but "
                    "proof.json was not created."
                )

            if not public_path.exists():
                raise RuntimeError(
                    "Proof generation completed but "
                    "public.json was not created."
                )

            # ==========================================
            # Load generated proof
            # ==========================================

            proof = json.loads(
                proof_path.read_text(
                    encoding="utf-8"
                )
            )

            public_signals = json.loads(
                public_path.read_text(
                    encoding="utf-8"
                )
            )

            # ==========================================
            # Return result
            # ==========================================

            return ProofResult(
                success=True,
                proof=proof,
                public_signals=public_signals,
                witness_time_ms=(
                    witness_end
                    - witness_start
                ) * 1000,
                proof_time_ms=(
                    proof_end
                    - proof_start
                ) * 1000,
            )