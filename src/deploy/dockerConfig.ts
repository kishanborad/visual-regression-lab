import type { DiffConfig } from '../types';

export function generateDockerConfig(config: DiffConfig): { dockerfile: string; runCommand: string } {
  const aaFlag = config.antiAliasing ? ' --antialiasing' : '';

  const dockerfile = `FROM node:20-slim

# Install Chromium dependencies
RUN apt-get update && apt-get install -y \\
    chromium \\
    --no-install-recommends \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install comparison tools
RUN npm init -y && npm install pixelmatch pngjs playwright

# Copy test files
COPY . .

ENTRYPOINT ["node", "run-visual-diff.js"]
`;

  const runCommand = `docker run --rm -v $(pwd)/screenshots:/app/screenshots \\
  visual-regression-check \\
  --baseline /app/screenshots/baseline.png \\
  --candidate /app/screenshots/candidate.png \\
  --threshold ${config.threshold}${aaFlag} \\
  --gate ${config.gateThreshold}`;

  return { dockerfile, runCommand };
}
