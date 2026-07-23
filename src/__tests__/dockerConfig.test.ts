// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { generateDockerConfig } from '../deploy/dockerConfig';
import type { DiffConfig } from '../types';

const config: DiffConfig = {
  threshold: 15,
  antiAliasing: false,
  diffColor: '#ff00ff',
  diffAlpha: 80,
  gateThreshold: 1.0,
};

describe('generateDockerConfig', () => {
  it('includes threshold in docker run command', () => {
    const { runCommand } = generateDockerConfig(config);
    expect(runCommand).toContain('--threshold 15');
  });

  it('includes gate threshold in run command', () => {
    const { runCommand } = generateDockerConfig(config);
    expect(runCommand).toContain('1');
  });

  it('generates a valid Dockerfile', () => {
    const { dockerfile } = generateDockerConfig(config);
    expect(dockerfile).toContain('FROM');
    expect(dockerfile).toContain('RUN');
    expect(dockerfile).toContain('ENTRYPOINT');
  });

  it('uses headless chrome image', () => {
    const { dockerfile } = generateDockerConfig(config);
    expect(dockerfile).toContain('node');
  });
});
