# ZK-DarkPool AI

> **A privacy-preserving dark pool prototype that combines AI-based candidate routing with zero-knowledge proof verification for private order matching.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Circom](https://img.shields.io/badge/Circom-ZK%20Circuits-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

Traditional electronic markets require market participants to expose information that can reveal trading intent, such as order price, quantity, and direction. This creates information-leakage and market-impact concerns, especially for large institutional orders.

**ZK-DarkPool AI** is a research and engineering prototype for private order matching. It combines:

- **Private orders** whose sensitive price and quantity values are hidden through cryptographic commitments.
- **Zero-knowledge proofs** for validating order and match conditions without publicly exposing private values.
- **AI-based candidate routing** to reduce the number of potential matches sent to the expensive ZK verification stage.
- **Private matching and settlement** for candidates that pass the verification pipeline.
- **Benchmarking** to measure the trade-off between AI selection fraction, valid-match recall, ZK workload, and end-to-end latency.
- **FastAPI endpoints** for interacting with the prototype programmatically.
- **A dashboard** for visualizing benchmark results.

The central design idea is:

```text
Private Orders
      │
      ▼
Commitments + Order Validity Proof
      │
      ▼
Private Order Book
      │
      ▼
Candidate Generation
      │
      ▼
AI Candidate Router
      │
      ├── Eliminated candidates ──► Avoid ZK verification
      │
      ▼
Selected Candidates
      │
      ▼
ZK Match Verification
      │
      ▼
Private Matching
      │
      ▼
Settlement
```

---

## Why AI + ZK?

Zero-knowledge verification provides privacy and cryptographic validity, but verifying every possible candidate pair can be computationally expensive.

The AI routing layer is therefore used as a **candidate-reduction stage before ZK verification**:

```text
All candidate pairs
        │
        ▼
AI ranking / selection
        │
        ├── Low-priority candidates filtered early
        │
        ▼
Smaller candidate set
        │
        ▼
ZK verification
        │
        ▼
Verified matches
```

This creates a measurable trade-off:

- Lower AI selection fraction → lower ZK workload and latency.
- Higher AI selection fraction → higher valid-match recall.
- The benchmark evaluates this trade-off across multiple operating points.

---

# Key Features

## Privacy-Preserving Orders

Each private order contains sensitive information such as:

- Side (`BUY` / `SELL`)
- Private price
- Private volume

Sensitive values are represented through cryptographic commitments before entering the public-facing matching pipeline.

## Zero-Knowledge Order Verification

Order validity is checked using a proof generation and verification flow.

Conceptually:

```text
Private Order
    │
    ▼
Commitment Generation
    │
    ▼
ZK Proof Generation
    │
    ▼
Proof Verification
    │
    ▼
Public Order Metadata
```

The public representation can contain coarse market features and commitments while keeping private order values hidden.

## AI Candidate Routing

The candidate router ranks or selects a subset of possible order pairs before ZK verification.

The benchmark evaluates selection fractions:

- 10%
- 15%
- 20%
- 25%
- 30%
- 35%
- 40%
- 45%
- 50%

This allows the system to produce a smoother and more detailed trade-off curve than evaluating only a few selection points.

## ZK Match Verification

Selected candidate pairs are sent through the matching and verification pipeline.

Only candidates that satisfy the required match conditions are treated as valid matches.

## Settlement

Valid matches can proceed to the settlement layer.

## FastAPI Backend

The project exposes a lightweight backend for interacting with the pipeline.

Available endpoints:

```text
POST /orders
POST /match
GET  /metrics
GET  /proof-status
```

## Benchmarking and Visualization

The project includes an end-to-end benchmark that measures:

- Pipeline latency
- AI ranking latency
- ZK matching latency
- Candidate reduction
- ZK workload reduction
- Valid matches
- Recall
- Precision
- Settlement count

A dashboard can visualize the resulting benchmark data.

---

# System Architecture

```text
                    ┌─────────────────────┐
                    │   Client / API      │
                    └──────────┬──────────┘
                               │
                    POST /orders
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Private Order      │
                    │  Creation           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Cryptographic       │
                    │ Commitments         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Order Validity ZK   │
                    │ Proof               │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Private Order Book  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Candidate Generator │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ AI Candidate Router │
                    └───────┬────────┬────┘
                            │        │
                   Filtered │        │ Selected
                            │        ▼
                            │  ┌──────────────────┐
                            │  │ ZK Match Proof   │
                            │  │ Verification     │
                            │  └────────┬─────────┘
                            │           │
                            │           ▼
                            │  ┌──────────────────┐
                            │  │ Matching Engine  │
                            │  └────────┬─────────┘
                            │           │
                            │           ▼
                            │  ┌──────────────────┐
                            └─►│ Settlement Engine│
                               └──────────────────┘
```

---

# Project Structure

The following structure focuses on the files and directories relevant to the main GitHub codebase.

```text
zk-darkpool-ai/
│
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI application and API endpoints
│
├── circuits/
│   ├── order_validity.circom   # ZK circuit for private order validity
│   ├── match_compatibility...  # ZK circuit for match compatibility
│   └── README.md
│
├── scripts/
│   ├── compile_circuits.sh
│   ├── setup_proving.sh
│   ├── run_demo.sh
│   └── poseidon_commit.js
│
├── src/
│   ├── __init__.py
│   │
│   ├── ai/
│   │   └── candidate_router.py
│   │
│   ├── crypto/
│   │   ├── commitments.py
│   │   ├── prover.py
│   │   └── verifier.py
│   │
│   ├── exchange/
│   │   ├── candidate_generator.py
│   │   ├── matching_engine.py
│   │   ├── private_order_book.py
│   │   └── settlement.py
│   │
│   ├── models/
│   │   └── order.py
│   │
│   └── utils/
│
├── benchmarks/
│   └── end_to_end_benchmark.py # End-to-end AI + ZK benchmark
│
├── app.py                      # CLI/demo application
├── dashboard.py                # Benchmark visualization dashboard
├── config.yaml                 # Project configuration
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies for ZK tooling
├── package-lock.json
├── .gitignore
├── LICENSE
└── README.md
```

> Generated artifacts such as benchmark result JSON files, graphs, compiled circuit outputs, proving artifacts, virtual environments, and `node_modules` should generally not be committed unless intentionally required for reproducibility or deployment.

---

# Installation

## 1. Clone the repository

```bash
git clone <your-repository-url>
cd zk-darkpool-ai
```

## 2. Create and activate a Python virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 4. Install Node.js dependencies

The ZK circuit tooling may require the dependencies defined in `package.json`.

```bash
npm install
```

## 5. Configure and compile the ZK circuits

Use the repository scripts and circuit setup appropriate to your local environment.

Typical workflow:

```bash
cd scripts
./compile_circuits.sh
./setup_proving.sh
```

On Windows, these shell scripts may require WSL, Git Bash, or an equivalent shell environment.

---

# Running the API

Start the FastAPI server from the repository root:

```bash
uvicorn api.main:app --reload
```

The server will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI automatically provides interactive documentation at:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### `POST /orders`

Submits a private order to the prototype.

Example request:

```json
{
  "side": "BUY",
  "price": 100.0,
  "quantity": 10
}
```

Example response:

```json
{
  "success": true,
  "message": "Private order submitted successfully",
  "order_id": 2,
  "side": "BUY",
  "price": "hidden",
  "quantity": "hidden",
  "commitment_generated": true,
  "order_proof_valid": true
}
```

The response intentionally does not expose the submitted private price or quantity.

---

### `POST /match`

Runs the matching pipeline using a selected AI routing fraction.

Example request:

```json
{
  "selection_fraction": 0.25
}
```

Example response:

```json
{
  "success": true,
  "selection_fraction": 0.25,
  "ai_selected": 25,
  "ai_eliminated": 75,
  "sent_to_zk": 15,
  "filtered_before_zk": 10,
  "valid_matches": 15,
  "settlements": 15,
  "recall": 0.283,
  "precision": 1.0,
  "zk_match_verified": true,
  "settlement_complete": true
}
```

---

### `GET /metrics`

Returns benchmark and pipeline metrics exposed by the backend.

Use:

```bash
curl http://127.0.0.1:8000/metrics
```

---

### `GET /proof-status`

Returns the current high-level proof and settlement status.

Use:

```bash
curl http://127.0.0.1:8000/proof-status
```

Example response:

```json
{
  "success": true,
  "private_orders_submitted": 3,
  "commitments_generated": true,
  "order_proof_valid": true,
  "zk_match_verified": true,
  "settlement_complete": true
}
```

---

# Running the CLI Demo

The repository also includes a direct Python demo that executes the core flow:

```bash
python app.py
```

The demo performs the following steps:

1. Creates private BUY and SELL orders.
2. Generates cryptographic commitments.
3. Generates and verifies order proofs.
4. Adds public metadata to the private order book.
5. Generates candidate matches.
6. Uses the AI router to select candidates.
7. Builds private match inputs.
8. Runs the matching engine.
9. Verifies valid matches.
10. Executes settlement for valid matches.

---

# Running the End-to-End Benchmark

Run:

```bash
python benchmarks/end_to_end_benchmark.py
```

The benchmark compares the baseline pipeline against multiple AI selection fractions.

The current benchmark sweep includes:

```text
10%, 15%, 20%, 25%, 30%, 35%, 40%, 45%, 50%
```

The benchmark output records latency and matching metrics for each operating point.

---

# Benchmark Metrics

## Baseline

The baseline represents the pipeline without the AI candidate-reduction stage.

Metrics include:

- Mean latency
- Median latency
- P95 latency
- Standard deviation
- Minimum latency
- Maximum latency
- Candidate count
- Candidates sent to ZK
- Candidates filtered before ZK
- Valid matches
- Settlements

## AI + ZK Pipeline

For each selection fraction, the benchmark records:

### Candidate metrics

- AI selected candidates
- AI eliminated candidates
- Candidate reduction percentage
- Candidates sent to ZK
- Candidates filtered before ZK

### ZK efficiency

- ZK work reduction percentage
- ZK matching latency

### Matching quality

- Valid matches
- Recall
- Precision
- Settlements

### Latency

- AI ranking latency
- End-to-end pipeline latency
- Latency reduction relative to the baseline

---

# Interpreting Recall and Precision

## Recall

Recall measures the fraction of baseline-valid matches recovered by the selected AI candidate set.

Conceptually:

```text
Recall =
Valid matches recovered by AI + ZK
──────────────────────────────────
Total baseline-valid matches
```

A higher selection fraction generally gives the router more candidate pairs to evaluate, which can increase recall.

## Precision

Precision measures the fraction of selected candidates that become valid matches.

Conceptually:

```text
Precision =
Valid matches
─────────────
Selected candidates
```

If the benchmark reports `100% precision`, it means that every candidate counted by that evaluation stage as a predicted match was valid according to the implemented benchmark logic. This should be interpreted together with recall: high precision alone does not guarantee that all possible valid matches were recovered.

---

# Benchmark Trade-Off

The benchmark is designed to demonstrate the following relationship:

```text
Lower Selection Fraction
        │
        ├── Fewer candidates processed
        ├── Less ZK work
        ├── Lower pipeline latency
        └── Potentially lower recall

Higher Selection Fraction
        │
        ├── More candidates processed
        ├── More ZK work
        ├── Higher pipeline latency
        └── Potentially higher recall
```

The objective is not simply to maximize candidate reduction or recall independently. The objective is to identify useful operating points where privacy-preserving verification remains efficient while preserving a meaningful portion of valid matches.

---

## Performance Graphs

The benchmark generates graphs dynamically from `end_to_end_benchmark.json`.


### Selection Fraction vs Valid Match Recall

Insert the generated graph here after running the benchmark:

```text
results/figures/selection_fraction_vs_valid_match_recall.png
```

![Selection Fraction vs Valid Match Recall](results/figures/selection_fraction_vs_valid_match_recall.png)

### AI Candidate Reduction vs ZK Work Reduction

Insert the generated graph here after running the benchmark:

```text
results/figures/ai_candidate_reduction_vs_zk_work.png
```

![AI Candidate Reduction vs ZK Work Reduction](results/figures/ai_candidate_reduction_vs_zk_work.png)

---

# Dashboard

Run the dashboard from the repository root:

```bash
python dashboard.py
```

The dashboard reads the benchmark output and presents key comparisons such as:

- Selection fraction vs valid-match recall
- Selection fraction vs pipeline latency
- Candidate reduction vs ZK work reduction
- Baseline performance
- Matching and settlement metrics

Run the end-to-end benchmark before opening the dashboard so that benchmark data is available.

---

# Technology Stack

| Component | Technology |
|---|---|
| Core implementation | Python |
| API | FastAPI |
| API server | Uvicorn |
| AI routing | Python-based candidate routing |
| Cryptographic commitments | Poseidon-style commitment workflow |
| Zero-knowledge circuits | Circom |
| ZK tooling | Node.js ecosystem |
| Benchmarking | Python |
| Visualization | Python dashboard |
| Parallel execution | CPU worker-based parallelism |

---

# API Workflow Example

```text
1. POST /orders
       │
       ▼
   Private order created
       │
       ▼
   Commitment generated
       │
       ▼
   Order proof verified

2. POST /orders
       │
       ▼
   Opposite-side private order created

3. POST /match
       │
       ▼
   Candidate generation
       │
       ▼
   AI selection
       │
       ▼
   ZK verification
       │
       ▼
   Valid match
       │
       ▼
   Settlement

4. GET /proof-status
       │
       ▼
   Inspect high-level pipeline status
```

---

# Design Goals

This prototype is designed around the following goals:

1. **Privacy** — sensitive order values should not be unnecessarily exposed.
2. **Verifiability** — important validity conditions should be checked cryptographically.
3. **Efficiency** — AI routing should reduce unnecessary expensive verification work.
4. **Measurability** — the performance trade-off should be benchmarked quantitatively.
5. **Usability** — the core prototype should be accessible through a lightweight API.
6. **Extensibility** — individual AI, cryptographic, matching, and API components should remain modular.

---

# Current Scope

This repository is a **prototype and research-oriented system** demonstrating an AI-assisted privacy-preserving matching architecture.

It is not presented as a production-ready exchange or custody system.

A production deployment would require additional work in areas such as:

- Adversarial security review
- Cryptographic parameter and trusted-setup management
- Circuit audits
- Key management
- Authentication and authorization
- Persistent database storage
- Distributed infrastructure
- Fault tolerance
- Rate limiting
- Monitoring and observability
- Regulatory and compliance controls
- Real exchange connectivity
- Real-time market-data ingestion
- Queue-position-aware execution modelling
- Slippage and transaction-cost modelling
- Independent performance validation

---

# Reproducibility Notes

Benchmark results can vary depending on:

- CPU model
- Number of CPU threads
- Number of parallel ZK workers
- Operating system
- Python and Node.js versions
- Circuit setup
- Local machine load
- Market/candidate generation configuration

For meaningful comparisons, benchmark configurations should be recorded alongside the result JSON.

---

# Recommended `.gitignore` Coverage

The repository should normally ignore environment-specific and generated files such as:

```text
.venv/
__pycache__/
*.pyc
node_modules/
results/
*.png
.env
.DS_Store
```

Generated ZK artifacts should also be reviewed before committing because proving keys and compiled outputs can be large or environment-specific.

---

# License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this project in accordance with the terms of the MIT License.

See the [LICENSE](LICENSE) file for details.

---

---

# Disclaimer

This project is an engineering and research prototype. It is not financial advice and should not be treated as a production trading, settlement, exchange, custody, or cryptographic security system without independent validation, security review, and substantial production hardening.

