import type { GateStatus } from '../types';

export function evaluateGate(mismatchPercent: number, gateThreshold: number): GateStatus {
  return mismatchPercent <= gateThreshold ? 'pass' : 'fail';
}
