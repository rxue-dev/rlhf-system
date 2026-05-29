#!/usr/bin/env bash
#
# Export annotations from the running annotator backend, then run the
# preprocessing pipeline on the exported data.
#
# Usage: ./scripts/export_and_run.sh [--backend-url URL] [--pipeline-args ...]
#
# Requires: curl, python3 with pipeline dependencies installed
# Assumes the annotator backend is running (default: http://localhost:8000)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
EXPORT_PATH="$ROOT_DIR/pipeline/output/annotations_exported.jsonl"
PROCESSED_PATH="$ROOT_DIR/pipeline/output/annotations_processed.jsonl"

echo "=== Step 1: Export annotations from $BACKEND_URL ==="
HTTP_CODE=$(curl -s -o "$EXPORT_PATH" -w "%{http_code}" "$BACKEND_URL/export")

if [ "$HTTP_CODE" != "200" ]; then
    echo "ERROR: Backend returned HTTP $HTTP_CODE. Is the annotator running?"
    echo "  Start it with: cd annotator/backend && python -m uvicorn main:app"
    exit 1
fi

LINE_COUNT=$(wc -l < "$EXPORT_PATH" | tr -d ' ')
echo "  Exported $LINE_COUNT annotations to $EXPORT_PATH"

if [ "$LINE_COUNT" -eq 0 ]; then
    echo "  No annotations to process. Annotate some pairs first!"
    exit 0
fi

echo ""
echo "=== Step 2: Run preprocessing pipeline ==="
cd "$ROOT_DIR/pipeline"
python -m src.pipeline \
    --input "$EXPORT_PATH" \
    --output "$PROCESSED_PATH" \
    --min_response_length 50 \
    "$@"

echo ""
echo "=== Step 3: Summary ==="
python -m src.stats "$PROCESSED_PATH"

echo ""
echo "Done. Processed output: $PROCESSED_PATH"
