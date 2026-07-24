#!/usr/bin/env bash
set -euo pipefail

# Visual Regression Lab — Full Test Suite
# Runs both Python and JavaScript test suites

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FAILED=0

echo "================================================"
echo "  Visual Regression Lab — Full Test Suite"
echo "================================================"
echo ""

# Python tests
echo "▸ Python tests"
echo "  ────────────────────────────────────────"
cd "$PROJECT_ROOT/python"
if python3 -m pytest tests/ -v --tb=short 2>&1; then
    echo "  ✓ Python tests passed"
else
    echo "  ✗ Python tests FAILED"
    FAILED=1
fi
echo ""

# Frontend tests
echo "▸ Frontend tests (Vitest)"
echo "  ────────────────────────────────────────"
cd "$PROJECT_ROOT"
if npx vitest run 2>&1; then
    echo "  ✓ Frontend tests passed"
else
    echo "  ✗ Frontend tests FAILED"
    FAILED=1
fi
echo ""

# TypeScript type check
echo "▸ TypeScript type check"
echo "  ────────────────────────────────────────"
if npx tsc --noEmit 2>&1; then
    echo "  ✓ Type check passed"
else
    echo "  ✗ Type check FAILED"
    FAILED=1
fi
echo ""

# Build check
echo "▸ Production build"
echo "  ────────────────────────────────────────"
if npm run build 2>&1; then
    echo "  ✓ Build succeeded"
else
    echo "  ✗ Build FAILED"
    FAILED=1
fi
echo ""

echo "================================================"
if [ $FAILED -eq 0 ]; then
    echo "  All checks passed ✓"
else
    echo "  Some checks failed ✗"
    exit 1
fi
echo "================================================"
