from pathlib import Path
import secrets
import shutil
import subprocess


ROOT_DIR = Path(__file__).resolve().parents[2]


def random_nonce() -> int:
    return secrets.randbits(128)


def _get_node() -> str:
    node = (
        shutil.which("node")
        or shutil.which("nodejs")
    )

    if node is None:
        raise FileNotFoundError(
            "Could not find Node.js. "
            "Make sure nodejs is installed."
        )

    return node


def _get_npm() -> str:
    npm = (
        shutil.which("npm")
        or shutil.which("npm.cmd")
    )

    if npm is None:
        raise FileNotFoundError(
            "Could not find npm. "
            "Make sure npm is installed with Node.js."
        )

    return npm


def _ensure_node_modules() -> None:
    node_modules = ROOT_DIR / "node_modules"

    circomlibjs = (
        node_modules
        / "circomlibjs"
    )

    if circomlibjs.exists():
        return

    npm = _get_npm()

    result = subprocess.run(
        [
            npm,
            "install",
            "--omit=dev",
        ],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Failed to install Node.js dependencies.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


def poseidon_commit(
    value: int,
    nonce: int,
) -> int:

    script = (
        ROOT_DIR
        / "scripts"
        / "poseidon_commit.mjs"
    )

    if not script.exists():
        raise FileNotFoundError(
            f"Poseidon script not found: {script}"
        )

    node = _get_node()

    _ensure_node_modules()

    result = subprocess.run(
        [
            node,
            str(script),
            str(value),
            str(nonce),
        ],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Poseidon commitment generation failed.\n\n"
            f"Command:\n"
            f"{node} {script} {value} {nonce}\n\n"
            f"Return code: {result.returncode}\n\n"
            f"STDOUT:\n"
            f"{result.stdout}\n\n"
            f"STDERR:\n"
            f"{result.stderr}"
        )

    output = result.stdout.strip()

    if not output:
        raise RuntimeError(
            "Poseidon commitment generation "
            "produced no output."
        )

    try:
        return int(output)

    except ValueError as error:
        raise RuntimeError(
            "Poseidon commitment returned "
            "an invalid value.\n\n"
            f"Output:\n{output}\n\n"
            f"STDERR:\n{result.stderr}"
        ) from error
