import { useCallback, useState } from 'react';

interface Props {
  label: string;
  onImageLoad: (imageData: ImageData) => void;
}

export default function DropZone({ label, onImageLoad }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.type.match(/^image\/(png|jpeg|webp)$/)) return;
    const { loadImageFile } = await import('./imageLoader');
    const imageData = await loadImageFile(file);
    setFileName(file.name);
    onImageLoad(imageData);
  }, [onImageLoad]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/webp';
    input.onchange = () => {
      const file = input.files?.[0];
      if (file) handleFile(file);
    };
    input.click();
  };

  return (
    <div
      onClick={handleClick}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`flex-1 flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed cursor-pointer
        transition-all duration-200 ${
          dragOver
            ? 'border-vr-accent bg-vr-accent/5 shadow-glow'
            : 'border-vr-border hover:border-vr-borderHover hover:bg-white/[0.02]'
        }`}
    >
      {fileName ? (
        <>
          <div className="w-10 h-10 rounded-lg bg-vr-accent/10 flex items-center justify-center">
            <span className="text-vr-accent text-lg">✓</span>
          </div>
          <span className="text-sm text-vr-secondary">{fileName}</span>
          <span className="text-xs text-vr-muted">Click to replace</span>
        </>
      ) : (
        <>
          <div className="w-12 h-12 rounded-xl bg-vr-surface border border-vr-border flex items-center justify-center">
            <span className="text-vr-muted text-2xl">↓</span>
          </div>
          <span className="text-sm text-vr-secondary">{label}</span>
          <span className="text-xs text-vr-muted">PNG, JPG, or WEBP</span>
        </>
      )}
    </div>
  );
}
