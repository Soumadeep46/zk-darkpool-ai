#!/usr/bin/env bash

set -euo pipefail

mkdir -p build/order_validity
mkdir -p build/match_compatibility

circom circuits/order_validity.circom \
  --r1cs \
  --wasm \
  --sym \
  -o build/order_validity \
  -l node_modules

circom circuits/match_compatibility.circom \
  --r1cs \
  --wasm \
  --sym \
  -o build/match_compatibility \
  -l node_modules

echo "Circuits compiled successfully."