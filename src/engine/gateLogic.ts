import type { DiffResult, GateStatus } from '../types';

export function evaluateGate(result: DiffResult, gateThreshold: number): GateStatus {
  return result.mismatchPercent <= gateThreshold ? 'pass' : 'fail';
}
