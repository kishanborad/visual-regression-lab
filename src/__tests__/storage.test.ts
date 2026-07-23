// @vitest-environment node
import { describe, it, expect, beforeEach, vi } from 'vitest';

// In-memory localStorage mock for node environment
const store: Record<string, string> = {};
const localStorageMock = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => { store[key] = value; },
  removeItem: (key: string) => { delete store[key]; },
  clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
};

vi.stubGlobal('localStorage', localStorageMock);

import { saveSettings, loadSettings, saveIgnoreRegions, loadIgnoreRegions, saveLastScenario, loadLastScenario } from '../persistence/storage';
import { DEFAULT_CONFIG } from '../types';

beforeEach(() => {
  localStorage.clear();
});

describe('settings persistence', () => {
  it('returns defaults when nothing is saved', () => {
    expect(loadSettings()).toEqual(DEFAULT_CONFIG);
  });

  it('round-trips saved settings', () => {
    const custom = { ...DEFAULT_CONFIG, threshold: 25, antiAliasing: false };
    saveSettings(custom);
    expect(loadSettings()).toEqual(custom);
  });
});

describe('ignore regions persistence', () => {
  it('returns empty array for unknown scenario', () => {
    expect(loadIgnoreRegions('unknown')).toEqual([]);
  });

  it('round-trips regions for a scenario', () => {
    const regions = [{ id: 'r1', x: 10, y: 20, width: 50, height: 30 }];
    saveIgnoreRegions('button-shift', regions);
    expect(loadIgnoreRegions('button-shift')).toEqual(regions);
  });
});

describe('last scenario persistence', () => {
  it('returns button-shift by default', () => {
    expect(loadLastScenario()).toBe('button-shift');
  });

  it('round-trips last scenario', () => {
    saveLastScenario('font-change');
    expect(loadLastScenario()).toBe('font-change');
  });
});
