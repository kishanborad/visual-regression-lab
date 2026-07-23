// @vitest-environment node
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { DiffConfig, IgnoreRegion } from '../types';
import { DEFAULT_CONFIG } from '../types';

// Mock pyodideLoader so we can test diffEngine without loading Pyodide
vi.mock('../engine/pyodideLoader', () => ({
  loadPyodide: vi.fn(),
}));

describe('diffEngine module', () => {
  describe('DEFAULT_CONFIG values', () => {
    it('has the expected default threshold', () => {
      expect(DEFAULT_CONFIG.threshold).toBe(10);
    });

    it('has anti-aliasing enabled by default', () => {
      expect(DEFAULT_CONFIG.antiAliasing).toBe(true);
    });

    it('has the expected default diff color', () => {
      expect(DEFAULT_CONFIG.diffColor).toBe('#ff00ff');
    });

    it('has the expected default gate threshold', () => {
      expect(DEFAULT_CONFIG.gateThreshold).toBe(0.5);
    });
  });

  describe('hex color parsing (inline verification)', () => {
    function parseHexColor(hex: string): { r: number; g: number; b: number } {
      const clean = hex.replace('#', '');
      return {
        r: parseInt(clean.substring(0, 2), 16),
        g: parseInt(clean.substring(2, 4), 16),
        b: parseInt(clean.substring(4, 6), 16),
      };
    }

    it('parses #ff00ff to magenta (255,0,255)', () => {
      const { r, g, b } = parseHexColor('#ff00ff');
      expect(r).toBe(255);
      expect(g).toBe(0);
      expect(b).toBe(255);
    });

    it('parses #000000 to black', () => {
      const { r, g, b } = parseHexColor('#000000');
      expect(r).toBe(0);
      expect(g).toBe(0);
      expect(b).toBe(0);
    });

    it('parses #ffffff to white', () => {
      const { r, g, b } = parseHexColor('#ffffff');
      expect(r).toBe(255);
      expect(g).toBe(255);
      expect(b).toBe(255);
    });

    it('parses #1a2b3c correctly', () => {
      const { r, g, b } = parseHexColor('#1a2b3c');
      expect(r).toBe(0x1a);
      expect(g).toBe(0x2b);
      expect(b).toBe(0x3c);
    });
  });

  describe('ignore region mapping', () => {
    function mapRegions(
      regions: IgnoreRegion[],
    ): [number, number, number, number][] {
      return regions.map((r) => [r.x, r.y, r.width, r.height]);
    }

    it('maps empty regions array to empty array', () => {
      expect(mapRegions([])).toEqual([]);
    });

    it('maps a single region correctly', () => {
      const regions: IgnoreRegion[] = [
        { id: 'r1', x: 10, y: 20, width: 50, height: 60 },
      ];
      expect(mapRegions(regions)).toEqual([[10, 20, 50, 60]]);
    });

    it('maps multiple regions preserving order', () => {
      const regions: IgnoreRegion[] = [
        { id: 'r1', x: 0, y: 0, width: 10, height: 10 },
        { id: 'r2', x: 100, y: 200, width: 30, height: 40 },
      ];
      expect(mapRegions(regions)).toEqual([
        [0, 0, 10, 10],
        [100, 200, 30, 40],
      ]);
    });
  });

  describe('runDiff with mocked Pyodide', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('calls loadPyodide and resolves a DiffResult', async () => {
      const { loadPyodide } = await import('../engine/pyodideLoader');
      const mockToJs = vi.fn().mockReturnValue([
        new Uint8Array(400),
        5,
        9900,
        0.05,
        100,
      ]);
      const mockRunPythonAsync = vi
        .fn()
        .mockResolvedValueOnce(undefined) // script load
        .mockResolvedValueOnce({ toJs: mockToJs }); // compare_images call

      vi.mocked(loadPyodide).mockResolvedValue({
        runPythonAsync: mockRunPythonAsync,
        globals: { set: vi.fn() },
        toPy: (v: unknown) => v,
      });

      const { runDiff } = await import('../engine/diffEngine');

      const config: DiffConfig = { ...DEFAULT_CONFIG };
      const baseline = new Uint8ClampedArray(400);
      const candidate = new Uint8ClampedArray(400);

      const result = await runDiff(baseline, candidate, 10, 10, config, []);

      expect(loadPyodide).toHaveBeenCalledOnce();
      expect(result.mismatchCount).toBe(5);
      expect(result.totalPixels).toBe(9900);
      expect(result.mismatchPercent).toBe(0.05);
      expect(result.ignoredCount).toBe(100);
      expect(result.width).toBe(10);
      expect(result.height).toBe(10);
      expect(result.diffImageData).toBeInstanceOf(Uint8ClampedArray);
    });

    it('uses customScript when provided instead of DEFAULT_DIFF_SCRIPT', async () => {
      const { loadPyodide } = await import('../engine/pyodideLoader');
      const allScripts: string[] = [];
      const mockToJs = vi.fn().mockReturnValue([new Uint8Array(0), 0, 100, 0, 0]);
      const mockRunPythonAsync = vi.fn().mockImplementation(async (s: string) => {
        allScripts.push(s as string);
        // Return diff result for the compare_images call (second call)
        if (allScripts.length === 2) {
          return { toJs: mockToJs };
        }
        return undefined;
      });

      vi.mocked(loadPyodide).mockResolvedValue({
        runPythonAsync: mockRunPythonAsync,
        globals: { set: vi.fn() },
        toPy: (v: unknown) => v,
      });

      const { runDiff } = await import('../engine/diffEngine');
      const customScript = 'def compare_images(): pass';
      await runDiff(
        new Uint8ClampedArray(0),
        new Uint8ClampedArray(0),
        1,
        1,
        DEFAULT_CONFIG,
        [],
        customScript,
      );

      // First call should be the customScript, not the DEFAULT_DIFF_SCRIPT
      expect(allScripts[0]).toBe(customScript);
    });
  });
});
