#!/usr/bin/env bash
set -euo pipefail

# Visual Regression Lab — Deploy to GitHub Pages

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "================================================"
echo "  Visual Regression Lab — Deploy"
echo "================================================"
echo ""

# Run full test suite first
echo "Running test suite before deploy..."
bash scripts/test.sh
echo ""

# Build
echo "Building production bundle..."
npm run build
echo ""

# Deploy
echo "Deploying to GitHub Pages..."
npx gh-pages -d dist
echo ""

echo "================================================"
echo "  Deployed successfully!"
echo "  URL: https://kishanborad.github.io/visual-regression-lab/"
echo "================================================"
