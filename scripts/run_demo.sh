#!/usr/bin/env bash

set -e

echo "Starting ZK-DarkPool AI demo..."

python -m src.ai.train_router

echo ""
echo "Running application..."

python app.py

echo ""
echo "Demo completed successfully."