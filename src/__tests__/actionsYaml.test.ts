// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { generateActionsYaml } from '../deploy/actionsYaml';
import type { DiffConfig } from '../types';

const config: DiffConfig = {
  threshold: 10,
  antiAliasing: true,
  diffColor: '#ff00ff',
  diffAlpha: 80,
  gateThreshold: 0.5,
};

describe('generateActionsYaml', () => {
  it('includes the threshold value', () => {
    const yaml = generateActionsYaml(config);
    expect(yaml).toContain('--threshold 10');
  });

  it('includes the gate threshold', () => {
    const yaml = generateActionsYaml(config);
    expect(yaml).toContain('0.5');
  });

  it('includes anti-aliasing flag when enabled', () => {
    const yaml = generateActionsYaml(config);
    expect(yaml).toContain('--antialiasing');
  });

  it('excludes anti-aliasing flag when disabled', () => {
    const yaml = generateActionsYaml({ ...config, antiAliasing: false });
    expect(yaml).not.toContain('--antialiasing');
  });

  it('is valid YAML structure', () => {
    const yaml = generateActionsYaml(config);
    expect(yaml).toContain('name:');
    expect(yaml).toContain('on:');
    expect(yaml).toContain('jobs:');
    expect(yaml).toContain('steps:');
  });
});
