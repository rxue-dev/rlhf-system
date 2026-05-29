"""Orchestrate the full RLHF data preprocessing pipeline."""

import argparse
import json
import sys
import time

from src.ingest import ingest
from src.filter import filter_rows
from src.reformat import reformat_and_write
from src.stats import run as run_stats


def load_local_jsonl(path: str) -> list:
    """Load a local JSONL file (e.g. exported from the annotator) into row dicts."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                record = json.loads(line)
                rows.append({
                    "chosen": f"Human: {record['prompt']}\n\nAssistant: {record['chosen']}",
                    "rejected": f"Human: {record['prompt']}\n\nAssistant: {record['rejected']}",
                })
    print(f"\n--- Local Ingest ---")
    print(f"File:         {path}")
    print(f"Rows loaded:  {len(rows)}")
    print()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end RLHF data preprocessing pipeline. "
        "Downloads Anthropic's HH-RLHF dataset (or reads a local JSONL file), "
        "filters for quality, and outputs training-ready JSONL."
    )
    parser.add_argument(
        "--input", default=None,
        help="Local JSONL file to process (skips HuggingFace download)"
    )
    parser.add_argument(
        "--split", default="train",
        help="Dataset split to process (default: train)"
    )
    parser.add_argument(
        "--max_samples", type=int, default=None,
        help="Maximum number of samples to load (default: all)"
    )
    parser.add_argument(
        "--min_response_length", type=int, default=50,
        help="Minimum character length for both chosen and rejected responses (default: 50)"
    )
    parser.add_argument(
        "--output", default="output/hh_rlhf_processed.jsonl",
        help="Output JSONL file path (default: output/hh_rlhf_processed.jsonl)"
    )
    args = parser.parse_args()

    start = time.time()

    print("=" * 50)
    print("  RLHF Data Preprocessing Pipeline")
    print("=" * 50)

    print("\n[1/4] Ingesting dataset...")
    if args.input:
        rows = load_local_jsonl(args.input)
    else:
        rows = ingest(split=args.split, max_samples=args.max_samples)

    if not rows:
        print("Error: no data ingested.", file=sys.stderr)
        sys.exit(1)

    print("[2/4] Filtering for quality...")
    filtered = filter_rows(rows, min_response_length=args.min_response_length)

    if not filtered:
        print("Error: all rows filtered out. Try lowering --min_response_length.", file=sys.stderr)
        sys.exit(1)

    print("[3/4] Reformatting to JSONL...")
    reformat_and_write(filtered, output_path=args.output, split=args.split)

    print("[4/4] Generating summary report...")
    run_stats(args.output)

    elapsed = time.time() - start
    print(f"Pipeline complete in {elapsed:.1f}s")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
