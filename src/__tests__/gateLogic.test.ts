// @vitest-environment node
import { describe, it, expect } from 'vitest';
import { evaluateGate } from '../engine/gateLogic';
import type { DiffResult } from '../types';

function makeResult(mismatchPercent: number): DiffResult {
  return {
    mismatchCount: mismatchPercent * 100,
    totalPixels: 10000,
    mismatchPercent,
    diffImageData: new Uint8ClampedArray(0),
    width: 100,
    height: 100,
    ignoredCount: 0,
  };
}

describe('evaluateGate', () => {
  it('returns pass when mismatch is below threshold', () => {
    expect(evaluateGate(makeResult(0.3), 0.5)).toBe('pass');
  });

  it('returns fail when mismatch exceeds threshold', () => {
    expect(evaluateGate(makeResult(1.2), 0.5)).toBe('fail');
  });

  it('returns pass at exact boundary', () => {
    expect(evaluateGate(makeResult(0.5), 0.5)).toBe('pass');
  });

  it('returns pass for zero mismatch', () => {
    expect(evaluateGate(makeResult(0), 0.5)).toBe('pass');
  });

  it('returns fail for 100% mismatch', () => {
    expect(evaluateGate(makeResult(100), 50)).toBe('fail');
  });
});
