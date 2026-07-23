// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { evaluateGate } from '../engine/gateLogic';

describe('evaluateGate', () => {
  it('returns pass when mismatch is below threshold', () => {
    expect(evaluateGate(0.3, 0.5)).toBe('pass');
  });

  it('returns fail when mismatch exceeds threshold', () => {
    expect(evaluateGate(1.2, 0.5)).toBe('fail');
  });

  it('returns pass at exact boundary', () => {
    expect(evaluateGate(0.5, 0.5)).toBe('pass');
  });

  it('returns pass for zero mismatch', () => {
    expect(evaluateGate(0, 0.5)).toBe('pass');
  });

  it('returns fail for 100% mismatch', () => {
    expect(evaluateGate(100, 50)).toBe('fail');
  });
});
