import type { DiffConfig, DiffResult, IgnoreRegion } from '../types';
import { loadPyodide } from './pyodideLoader';
import { DEFAULT_DIFF_SCRIPT } from './diffScript';

export async function runDiff(
  baselineData: Uint8ClampedArray,
  candidateData: Uint8ClampedArray,
  width: number,
  height: number,
  config: DiffConfig,
  ignoreRegions: IgnoreRegion[],
  customScript?: string,
): Promise<DiffResult> {
  const pyodide = await loadPyodide();

  const script = customScript ?? DEFAULT_DIFF_SCRIPT;
  await pyodide.runPythonAsync(script);

  // Convert diff color hex to RGB
  const hex = config.diffColor.replace('#', '');
  const diffR = parseInt(hex.substring(0, 2), 16);
  const diffG = parseInt(hex.substring(2, 4), 16);
  const diffB = parseInt(hex.substring(4, 6), 16);

  // Convert ignore regions to Python list of tuples
  const regions = ignoreRegions.map((r) => [r.x, r.y, r.width, r.height]);

  // Pass pixel data to Python
  pyodide.globals.set('_baseline_bytes', pyodide.toPy(new Uint8Array(baselineData.buffer)));
  pyodide.globals.set('_candidate_bytes', pyodide.toPy(new Uint8Array(candidateData.buffer)));

  const result = await pyodide.runPythonAsync(`
compare_images(
    bytes(_baseline_bytes),
    bytes(_candidate_bytes),
    ${width}, ${height},
    ${config.threshold}, ${config.antiAliasing ? 'True' : 'False'},
    ${diffR}, ${diffG}, ${diffB}, ${config.diffAlpha},
    ${JSON.stringify(regions)}
)
  `);

  const [diffBytes, mismatchCount, totalPixels, mismatchPercent, ignoredCount] = result.toJs();

  const diffArray = new Uint8ClampedArray(
    diffBytes instanceof ArrayBuffer ? diffBytes : new Uint8Array(diffBytes).buffer,
  );

  return {
    mismatchCount,
    totalPixels,
    mismatchPercent: Math.round(mismatchPercent * 100) / 100,
    diffImageData: diffArray,
    width,
    height,
    ignoredCount,
  };
}
