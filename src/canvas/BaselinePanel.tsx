import { useRef, useEffect, useCallback, useState } from 'react';
import type { IgnoreRegion } from '../types';
import { createRegion, drawIgnoreRegions, hitTestDeleteButton } from './ignoreRegions';

interface Props {
  imageData: ImageData | null;
  ignoreRegions: IgnoreRegion[];
  drawingEnabled: boolean;
  onRegionsChange: (regions: IgnoreRegion[]) => void;
}

export default function BaselinePanel({ imageData, ignoreRegions, drawingEnabled, onRegionsChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [drawing, setDrawing] = useState(false);
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null);

  const getScale = useCallback(() => {
    if (!canvasRef.current || !imageData) return 1;
    return canvasRef.current.clientWidth / imageData.width;
  }, [imageData]);

  // Render image
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageData) return;
    canvas.width = imageData.width;
    canvas.height = imageData.height;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.putImageData(imageData, 0, 0);
  }, [imageData]);

  // Render ignore region overlay
  useEffect(() => {
    const overlay = overlayRef.current;
    const canvas = canvasRef.current;
    if (!overlay || !canvas || !imageData) return;
    overlay.width = canvas.clientWidth * window.devicePixelRatio;
    overlay.height = canvas.clientHeight * window.devicePixelRatio;
    const ctx = overlay.getContext('2d');
    if (!ctx) return;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    drawIgnoreRegions(ctx, ignoreRegions, getScale());
  }, [ignoreRegions, imageData, getScale]);

  const getCanvasCoords = (e: React.MouseEvent) => {
    const rect = overlayRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!drawingEnabled || !imageData) return;
    const { x, y } = getCanvasCoords(e);
    const scale = getScale();

    // Check if clicking delete button
    const deleteId = hitTestDeleteButton(ignoreRegions, x, y, scale);
    if (deleteId) {
      onRegionsChange(ignoreRegions.filter((r) => r.id !== deleteId));
      return;
    }

    setDrawing(true);
    setStartPos({ x, y });
  }, [drawingEnabled, imageData, ignoreRegions, onRegionsChange, getScale]);

  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    if (!drawing || !startPos || !imageData) return;
    const { x, y } = getCanvasCoords(e);
    const scale = getScale();

    const rx = Math.round(Math.min(startPos.x, x) / scale);
    const ry = Math.round(Math.min(startPos.y, y) / scale);
    const rw = Math.round(Math.abs(x - startPos.x) / scale);
    const rh = Math.round(Math.abs(y - startPos.y) / scale);

    if (rw > 5 && rh > 5) {
      const region = createRegion(rx, ry, rw, rh);
      onRegionsChange([...ignoreRegions, region]);
    }

    setDrawing(false);
    setStartPos(null);
  }, [drawing, startPos, imageData, ignoreRegions, onRegionsChange, getScale]);

  return (
    <div ref={containerRef} className="relative w-full h-full flex flex-col">
      <div className="px-3 py-2 border-b border-vr-border flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-vr-accent"></div>
        <span className="text-xs font-medium text-vr-secondary uppercase tracking-widest">Baseline</span>
      </div>
      <div className="flex-1 relative overflow-hidden p-2">
        <canvas
          ref={canvasRef}
          className="w-full h-full object-contain rounded-lg"
          style={{ imageRendering: 'pixelated' }}
        />
        <canvas
          ref={overlayRef}
          className="absolute inset-2 w-[calc(100%-16px)] h-[calc(100%-16px)]"
          style={{ cursor: drawingEnabled ? 'crosshair' : 'default' }}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
        />
      </div>
    </div>
  );
}
