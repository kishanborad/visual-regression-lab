interface Props {
  value: number;
  onChange: (value: number) => void;
}

export default function AlphaSlider({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <label className="text-xs text-vr-secondary">Diff Alpha</label>
        <span className="text-xs font-mono text-vr-accent">{value}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        step={1}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        className="slider-track"
      />
    </div>
  );
}
