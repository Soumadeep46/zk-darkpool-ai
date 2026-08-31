#!/usr/bin/env bash

set -euo pipefail

mkdir -p artifacts

PTAU="artifacts/pot12_final.ptau"

if [ ! -f "$PTAU" ]; then
  snarkjs powersoftau new bn128 12 \
    artifacts/pot12_0000.ptau \
    -v

  snarkjs powersoftau contribute \
    artifacts/pot12_0000.ptau \
    artifacts/pot12_0001.ptau \
    --name="local-development-contribution" \
    -e="${ZK_ENTROPY:-change-this-development-entropy}" \
    -v

  snarkjs powersoftau prepare phase2 \
    artifacts/pot12_0001.ptau \
    "$PTAU" \
    -v
fi

for CIRCUIT in order_validity match_compatibility; do
  snarkjs groth16 setup \
    "build/$CIRCUIT/$CIRCUIT.r1cs" \
    "$PTAU" \
    "artifacts/${CIRCUIT}_0000.zkey"

  snarkjs zkey contribute \
    "artifacts/${CIRCUIT}_0000.zkey" \
    "artifacts/${CIRCUIT}_final.zkey" \
    --name="local-development-phase2" \
    -e="${ZK_ENTROPY:-change-this-development-entropy}" \
    -v

  snarkjs zkey export verificationkey \
    "artifacts/${CIRCUIT}_final.zkey" \
    "artifacts/${CIRCUIT}_verification_key.json"
done

echo "Proving setup completed successfully."