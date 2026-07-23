interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function ColorPicker({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-vr-secondary">Diff Color</label>
      <div className="relative">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-8 h-8 rounded-lg cursor-pointer border border-vr-border bg-transparent
                     [&::-webkit-color-swatch-wrapper]:p-0.5
                     [&::-webkit-color-swatch]:rounded-md [&::-webkit-color-swatch]:border-0"
        />
      </div>
      <span className="text-xs font-mono text-vr-muted">{value}</span>
    </div>
  );
}
