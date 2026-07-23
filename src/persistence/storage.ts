import type { DiffConfig, IgnoreRegion } from '../types';
import { DEFAULT_CONFIG } from '../types';

const SETTINGS_KEY = 'vr-lab-settings';
const REGIONS_KEY_PREFIX = 'vr-lab-regions-';
const SCENARIO_KEY = 'vr-lab-last-scenario';

export function saveSettings(config: DiffConfig): void {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(config));
}

export function loadSettings(): DiffConfig {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (!raw) return DEFAULT_CONFIG;
  try {
    const parsed = JSON.parse(raw);
    return { ...DEFAULT_CONFIG, ...parsed };
  } catch {
    return DEFAULT_CONFIG;
  }
}

export function saveIgnoreRegions(scenarioId: string, regions: IgnoreRegion[]): void {
  localStorage.setItem(REGIONS_KEY_PREFIX + scenarioId, JSON.stringify(regions));
}

export function loadIgnoreRegions(scenarioId: string): IgnoreRegion[] {
  const raw = localStorage.getItem(REGIONS_KEY_PREFIX + scenarioId);
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function saveLastScenario(id: string): void {
  localStorage.setItem(SCENARIO_KEY, id);
}

export function loadLastScenario(): string {
  return localStorage.getItem(SCENARIO_KEY) || 'button-shift';
}
