# RLHF System

An end-to-end system for understanding how Reinforcement Learning from Human Feedback works — from collecting human preferences to producing training-ready data. Built as a learning project to make every decision in the RLHF data pipeline visible and auditable.

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                           RLHF System                                  │
│                                                                        │
│  ┌──────────────────────┐         ┌──────────────────────────────┐    │
│  │      annotator/       │         │          pipeline/            │    │
│  │                       │         │                              │    │
│  │  React frontend       │         │  ingest.py  (HF or local)   │    │
│  │  FastAPI backend      │  JSONL  │  filter.py  (quality gates) │    │
│  │  SQLite database      │────────▶│  reformat.py (TRL format)   │    │
│  │                       │         │  stats.py   (summary)       │    │
│  │  Human annotators     │         │                              │    │
│  │  compare response     │         │  Output: training-ready      │    │
│  │  pairs (A vs B)       │         │  JSONL for reward models     │    │
│  └──────────────────────┘         └──────────────────────────────┘    │
│              │                                    ▲                     │
│              └────────────────────────────────────┘                     │
│                     scripts/export_and_run.sh                           │
└────────────────────────────────────────────────────────────────────────┘
```

## Components

### `annotator/` — Human Preference Collection

A full-stack annotation interface for pairwise LLM response comparison. Given a prompt and two model responses, an annotator chooses which is better. Features:

- **Least-annotated-first queue** — maximizes dataset coverage
- **Position randomization** — detects and controls for position bias via `response_a_shown_as`
- **JSONL export** — Anthropic HH-RLHF compatible schema

### `pipeline/` — Data Preprocessing

Downloads Anthropic's HH-RLHF dataset (or accepts local JSONL from the annotator), applies configurable quality filters, and outputs training-ready JSONL for TRL's RewardTrainer/SFTTrainer. Filters:

- Duplicate responses (zero preference signal)
- Minimum response length
- Junk patterns (dots, "N/A", filler)
- Toxic content (auditable blocklist, no ML dependencies)

### `scripts/export_and_run.sh` — The Glue

One command that exports annotations from the running backend and feeds them through the pipeline:

```bash
./scripts/export_and_run.sh
```

This makes the connection between the two components tangible and runnable.

## Quick Start

### 1. Start the annotator

```bash
cd annotator/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# In another terminal:
cd annotator/frontend
npm install
npm run dev
```

Open http://localhost:5173, enter an annotator name, and label some pairs.

### 2. Run the full pipeline on your annotations

```bash
pip install -r pipeline/requirements.txt
./scripts/export_and_run.sh
```

### 3. Or run the pipeline on Anthropic's HH-RLHF dataset

```bash
cd pipeline
python -m src.pipeline --split train --max_samples 5000
```

## Testing

```bash
# Pipeline filter tests
cd pipeline && python -m pytest tests/ -v

# Annotator queue logic tests
cd annotator/backend && python -m pytest tests/ -v
```

## Project Structure

```
rlhf-system/
├── annotator/
│   ├── frontend/       React + Vite annotation UI
│   └── backend/        FastAPI + SQLite
├── pipeline/
│   ├── src/            ingest → filter → reformat → stats
│   ├── tests/          Unit tests for filter heuristics
│   └── output/         Generated JSONL files
├── scripts/
│   └── export_and_run.sh
└── README.md
```
