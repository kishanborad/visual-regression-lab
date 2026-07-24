#!/usr/bin/env bash
set -euo pipefail

# Visual Regression Lab — Development Setup
# Sets up both the Node.js frontend and Python comparison engine

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "  Visual Regression Lab — Development Setup"
echo "================================================"
echo ""

# Check prerequisites
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: $1 is not installed"
        echo "  Install it from: $2"
        exit 1
    fi
    echo "  ✓ $1 found: $(command -v "$1")"
}

echo "Checking prerequisites..."
check_command "node" "https://nodejs.org/"
check_command "npm" "https://nodejs.org/"
check_command "python3" "https://www.python.org/"
check_command "pip3" "https://pip.pypa.io/"

NODE_VERSION=$(node --version)
PYTHON_VERSION=$(python3 --version)
echo ""
echo "  Node.js: $NODE_VERSION"
echo "  Python:  $PYTHON_VERSION"
echo ""

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
cd "$PROJECT_ROOT"
npm install
echo "  ✓ Node.js dependencies installed"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$PROJECT_ROOT/python"
pip3 install -r requirements.txt
echo "  ✓ Python dependencies installed"
echo ""

# Run Python tests
echo "Running Python test suite..."
cd "$PROJECT_ROOT/python"
python3 -m pytest tests/ -v --tb=short
echo ""

# Run frontend tests
echo "Running frontend tests..."
cd "$PROJECT_ROOT"
npx vitest run
echo ""

# Type check
echo "Running TypeScript type check..."
npx tsc --noEmit
echo ""

echo "================================================"
echo "  Setup complete!"
echo ""
echo "  Start dev server:  npm run dev"
echo "  Run Python tests:  cd python && pytest tests/ -v"
echo "  Run all tests:     scripts/test.sh"
echo "  Build for prod:    npm run build"
echo "  Docker build:      docker build -t vr-lab ."
echo "================================================"
