from pathlib import Path
import secrets
import subprocess


ROOT_DIR = Path(__file__).resolve().parents[2]
POSEIDON_SCRIPT = ROOT_DIR / "scripts" / "poseidon_commit.mjs"


def random_nonce() -> int:
    return secrets.randbits(120)


def poseidon_commit(value: int, nonce: int) -> str:
    if value < 0 or nonce < 0:
        raise ValueError("Value and nonce must be non-negative")

    result = subprocess.run(
        [
            "node",
            str(POSEIDON_SCRIPT),
            str(value),
            str(nonce),
        ],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()