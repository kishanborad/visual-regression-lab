import { useRef, useEffect } from 'react';

interface Props {
  imageData: ImageData | null;
}

export default function CandidatePanel({ imageData }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageData) return;
    canvas.width = imageData.width;
    canvas.height = imageData.height;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.putImageData(imageData, 0, 0);
  }, [imageData]);

  return (
    <div className="relative w-full h-full flex flex-col">
      <div className="px-3 py-2 border-b border-vr-border flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-vr-accentDim"></div>
        <span className="text-xs font-medium text-vr-secondary uppercase tracking-widest">Candidate</span>
      </div>
      <div className="flex-1 relative overflow-hidden p-2">
        <canvas
          ref={canvasRef}
          className="w-full h-full object-contain rounded-lg"
          style={{ imageRendering: 'pixelated' }}
        />
      </div>
    </div>
  );
}
