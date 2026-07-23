import { useRef, useEffect } from 'react';
import type { DiffResult, GateStatus } from '../types';

interface Props {
  diffResult: DiffResult | null;
  gateStatus: GateStatus;
}

export default function DiffPanel({ diffResult, gateStatus }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !diffResult) return;
    canvas.width = diffResult.width;
    canvas.height = diffResult.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const imgData = new ImageData(
      new Uint8ClampedArray(diffResult.diffImageData.buffer as ArrayBuffer),
      diffResult.width,
      diffResult.height,
    );
    ctx.putImageData(imgData, 0, 0);
  }, [diffResult]);

  const glowClass = gateStatus === 'pass' ? 'shadow-glow-pass' : gateStatus === 'fail' ? 'shadow-glow-fail' : '';

  return (
    <div className={`relative w-full h-full flex flex-col transition-shadow duration-500 ${glowClass}`}>
      <div className="px-3 py-2 border-b border-vr-border flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${
          gateStatus === 'pass' ? 'bg-vr-pass' : gateStatus === 'fail' ? 'bg-vr-fail' : 'bg-vr-muted'
        }`}></div>
        <span className="text-xs font-medium text-vr-secondary uppercase tracking-widest">Diff</span>
      </div>
      <div className="flex-1 relative overflow-hidden p-2">
        {diffResult ? (
          <canvas
            ref={canvasRef}
            className="w-full h-full object-contain rounded-lg"
            style={{ imageRendering: 'pixelated' }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-vr-muted text-sm">
            Run diff to see results
          </div>
        )}
      </div>
    </div>
  );
}
