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

        self.wasm = (
            ROOT_DIR
            / "build"
            / circuit
            / f"{circuit}_js"
            / f"{circuit}.wasm"
        )

        self.zkey = (
            ROOT_DIR
            / "artifacts"
            / f"{circuit}_final.zkey"
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

    def _snarkjs_command(self) -> list[str]:
        return [
            self.npx,
            "--yes",
            "--package=snarkjs@0.7.6",
            "snarkjs",
        ]

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

            witness_start = time.perf_counter()

            witness_command = (
                self._snarkjs_command()
                + [
                    "wtns",
                    "calculate",
                    str(self.wasm),
                    str(input_path),
                    str(witness_path),
                ]
            )

            try:
                subprocess.run(
                    witness_command,
                    cwd=str(ROOT_DIR),
                    check=True,
                    capture_output=True,
                    text=True,
                )

            except FileNotFoundError as error:
                raise RuntimeError(
                    "Could not execute npx.\n"
                    f"Resolved npx path: {self.npx}"
                ) from error

            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "Witness generation failed.\n\n"
                    f"Circuit: {self.circuit}\n\n"
                    f"Command:\n"
                    f"{' '.join(witness_command)}\n\n"
                    f"Input:\n"
                    f"{json.dumps(input_data, indent=2)}\n\n"
                    f"STDOUT:\n"
                    f"{error.stdout}\n\n"
                    f"STDERR:\n"
                    f"{error.stderr}"
                ) from error

            witness_end = time.perf_counter()

            if not witness_path.exists():
                raise RuntimeError(
                    "Witness generation completed but "
                    "witness.wtns was not created.\n"
                    f"Expected path: {witness_path}"
                )

            proof_start = time.perf_counter()

            proof_command = (
                self._snarkjs_command()
                + [
                    "groth16",
                    "prove",
                    str(self.zkey),
                    str(witness_path),
                    str(proof_path),
                    str(public_path),
                ]
            )

            try:
                subprocess.run(
                    proof_command,
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
                    f"Command:\n"
                    f"{' '.join(proof_command)}\n\n"
                    f"STDOUT:\n"
                    f"{error.stdout}\n\n"
                    f"STDERR:\n"
                    f"{error.stderr}"
                ) from error

            proof_end = time.perf_counter()

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
