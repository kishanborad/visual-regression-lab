import type { IgnoreRegion } from '../types';

let nextId = 1;

export function createRegion(x: number, y: number, width: number, height: number): IgnoreRegion {
  return { id: `region-${nextId++}`, x, y, width, height };
}

export function drawIgnoreRegions(ctx: CanvasRenderingContext2D, regions: IgnoreRegion[], scale: number): void {
  regions.forEach((region) => {
    // Semi-transparent blue overlay
    ctx.fillStyle = 'rgba(99, 102, 241, 0.2)';
    ctx.fillRect(region.x * scale, region.y * scale, region.width * scale, region.height * scale);

    // Dashed border
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.6)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.strokeRect(region.x * scale, region.y * scale, region.width * scale, region.height * scale);
    ctx.setLineDash([]);

    // Delete button (X) in top-right corner
    const btnSize = 16;
    const btnX = (region.x + region.width) * scale - btnSize - 2;
    const btnY = region.y * scale + 2;
    ctx.fillStyle = 'rgba(239, 68, 68, 0.8)';
    ctx.beginPath();
    ctx.arc(btnX + btnSize / 2, btnY + btnSize / 2, btnSize / 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('✕', btnX + btnSize / 2, btnY + btnSize / 2);
  });
}

export function hitTestDeleteButton(
  regions: IgnoreRegion[],
  clickX: number,
  clickY: number,
  scale: number,
): string | null {
  for (const region of regions) {
    const btnSize = 16;
    const btnCenterX = (region.x + region.width) * scale - btnSize / 2 - 2;
    const btnCenterY = region.y * scale + btnSize / 2 + 2;
    const dist = Math.sqrt((clickX - btnCenterX) ** 2 + (clickY - btnCenterY) ** 2);
    if (dist <= btnSize / 2) return region.id;
  }
  return null;
}

export function serializeRegions(regions: IgnoreRegion[]): string {
  return JSON.stringify(regions);
}

export function deserializeRegions(json: string): IgnoreRegion[] {
  try {
    const parsed = JSON.parse(json);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (r: unknown) => {
        if (typeof r !== 'object' || r === null) return false;
        const obj = r as Record<string, unknown>;
        return typeof obj.id === 'string' && typeof obj.x === 'number' &&
               typeof obj.y === 'number' && typeof obj.width === 'number' &&
               typeof obj.height === 'number';
      },
    );
  } catch {
    return [];
  }
}
