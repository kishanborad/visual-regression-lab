#!/usr/bin/env bash
set -euo pipefail

# Visual Regression Lab — Docker Runner
# Build and run the comparison engine in Docker

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

IMAGE_NAME="visual-regression-lab"
THRESHOLD="${THRESHOLD:-10}"
GATE="${GATE:-0.5}"

cd "$PROJECT_ROOT"

echo "================================================"
echo "  Visual Regression Lab — Docker Runner"
echo "================================================"
echo ""

# Build the image
echo "Building Docker image..."
docker build -t "$IMAGE_NAME" .
echo "  ✓ Image built: $IMAGE_NAME"
echo ""

# Check for screenshot directories
if [ ! -d "screenshots/baseline" ] || [ ! -d "screenshots/candidate" ]; then
    echo "No screenshots found. Capturing..."
    bash scripts/capture-screenshots.sh
    echo ""
fi

# Create reports directory
mkdir -p reports

# Run comparison
echo "Running visual regression comparison..."
echo "  Threshold: $THRESHOLD%"
echo "  Gate:      $GATE%"
echo ""

docker run --rm \
    -v "$PROJECT_ROOT/screenshots:/app/screenshots:ro" \
    -v "$PROJECT_ROOT/reports:/app/reports" \
    "$IMAGE_NAME" \
    python batch_compare.py \
        --baseline-dir /app/screenshots/baseline \
        --candidate-dir /app/screenshots/candidate \
        --output-dir /app/reports \
        --threshold "$THRESHOLD" \
        --gate "$GATE"

echo ""

# Check results
if [ -f "reports/summary.json" ]; then
    python3 -c "
import json
with open('reports/summary.json') as f:
    s = json.load(f)
status = '✓ PASS' if s.get('gate_status') == 'pass' else '✗ FAIL'
print(f'  {status}: {s[\"passed_count\"]}/{s[\"total_count\"]} comparisons passed')
print(f'  Report: reports/report.html')
"
fi

echo ""
echo "================================================"
