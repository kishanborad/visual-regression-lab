import type { DiffConfig } from '../types';

export function generateActionsYaml(config: DiffConfig): string {
  const aaFlag = config.antiAliasing ? ' --antialiasing' : '';

  return `name: Visual Regression Test

on:
  pull_request:
    branches: [main]

jobs:
  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      - name: Capture baseline screenshots
        run: npx playwright test --project=baseline

      - name: Capture candidate screenshots
        run: npx playwright test --project=candidate

      - name: Run visual diff
        run: |
          npx pixelmatch \\
            screenshots/baseline.png \\
            screenshots/candidate.png \\
            screenshots/diff.png \\
            --threshold ${config.threshold}${aaFlag}

      - name: Evaluate gate (max ${config.gateThreshold}% mismatch)
        run: |
          MISMATCH=$(node -e "
            const fs = require('fs');
            const { PNG } = require('pngjs');
            const pixelmatch = require('pixelmatch');
            const base = PNG.sync.read(fs.readFileSync('screenshots/baseline.png'));
            const cand = PNG.sync.read(fs.readFileSync('screenshots/candidate.png'));
            const diff = new PNG({ width: base.width, height: base.height });
            const count = pixelmatch(base.data, cand.data, diff.data, base.width, base.height, { threshold: ${config.threshold / 100} });
            const pct = (count / (base.width * base.height) * 100).toFixed(2);
            console.log(pct);
          ")
          echo "Mismatch: \${MISMATCH}%"
          if (( $(echo "\${MISMATCH} > ${config.gateThreshold}" | bc -l) )); then
            echo "::error::Visual regression failed: \${MISMATCH}% exceeds ${config.gateThreshold}% gate"
            exit 1
          fi

      - name: Upload diff artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-diff
          path: screenshots/
          retention-days: 14
`;
}
