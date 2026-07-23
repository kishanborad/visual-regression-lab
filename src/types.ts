export interface DiffConfig {
  threshold: number;        // 0-100, color distance tolerance %
  antiAliasing: boolean;
  diffColor: string;        // hex, e.g. '#ff00ff'
  diffAlpha: number;        // 0-100, opacity %
  gateThreshold: number;    // 0-100, max allowed mismatch %
}

export interface DiffResult {
  mismatchCount: number;
  totalPixels: number;
  mismatchPercent: number;
  diffImageData: Uint8ClampedArray;
  width: number;
  height: number;
  ignoredCount: number;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  teaches: string;
  mutationClass: string;    // CSS class toggled on version B iframe
}

export interface IgnoreRegion {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface StatsData {
  totalPixels: number;
  mismatchCount: number;
  mismatchPercent: number;
  width: number;
  height: number;
  ignoredCount: number;
}

export type GateStatus = 'pass' | 'fail' | 'idle';

export const DEFAULT_CONFIG: DiffConfig = {
  threshold: 10,
  antiAliasing: true,
  diffColor: '#ff00ff',
  diffAlpha: 80,
  gateThreshold: 0.5,
};
