#!/usr/bin/env bash
set -euo pipefail

# Visual Regression Lab — Screenshot Capture
# Captures baseline and candidate screenshots for CI comparison

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BASELINE_DIR="${1:-$PROJECT_ROOT/screenshots/baseline}"
CANDIDATE_DIR="${2:-$PROJECT_ROOT/screenshots/candidate}"
PORT="${3:-4173}"

mkdir -p "$BASELINE_DIR" "$CANDIDATE_DIR"

echo "================================================"
echo "  Screenshot Capture"
echo "================================================"
echo ""
echo "  Baseline dir:  $BASELINE_DIR"
echo "  Candidate dir: $CANDIDATE_DIR"
echo "  Preview port:  $PORT"
echo ""

# Start preview server in background
echo "Starting preview server..."
cd "$PROJECT_ROOT"
npx vite preview --port "$PORT" &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
for i in $(seq 1 30); do
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        echo "  ✓ Server ready on port $PORT"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  ✗ Server failed to start"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo ""

# Capture screenshots for each scenario
SCENARIOS=("button-shift" "color-swap" "missing-element" "font-change" "spacing-collapse")

for scenario in "${SCENARIOS[@]}"; do
    echo "Capturing: $scenario"

    # Baseline (version A)
    npx playwright screenshot \
        --browser chromium \
        --viewport-size "800,600" \
        "http://localhost:$PORT/visual-regression-lab/scenarios.html?scenario=$scenario&version=a" \
        "$BASELINE_DIR/${scenario}.png" 2>/dev/null

    # Candidate (version B)
    npx playwright screenshot \
        --browser chromium \
        --viewport-size "800,600" \
        "http://localhost:$PORT/visual-regression-lab/scenarios.html?scenario=$scenario&version=b" \
        "$CANDIDATE_DIR/${scenario}.png" 2>/dev/null

    echo "  ✓ Captured baseline and candidate for $scenario"
done

echo ""

# Cleanup
echo "Stopping preview server..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "================================================"
echo "  Screenshots captured!"
echo "  Baseline:  $BASELINE_DIR/"
echo "  Candidate: $CANDIDATE_DIR/"
echo ""
echo "  Run comparison:"
echo "    cd python && python batch_compare.py \\"
echo "      --baseline-dir $BASELINE_DIR \\"
echo "      --candidate-dir $CANDIDATE_DIR \\"
echo "      --output-dir reports/"
echo "================================================"
