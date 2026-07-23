import type { StatsData } from '../types';

interface Props {
  stats: StatsData | null;
}

export default function StatsRow({ stats }: Props) {
  if (!stats) return null;

  const items = [
    { label: 'Total Pixels', value: stats.totalPixels.toLocaleString() },
    { label: 'Mismatched', value: stats.mismatchCount.toLocaleString() },
    { label: 'Mismatch %', value: `${stats.mismatchPercent.toFixed(2)}%` },
    { label: 'Dimensions', value: `${stats.width} × ${stats.height}` },
    { label: 'Ignored', value: stats.ignoredCount.toLocaleString() },
  ];

  return (
    <div className="flex items-center justify-center gap-6 py-2 animate-fade-in">
      {items.map((item) => (
        <div key={item.label} className="text-center">
          <div className="text-xs text-vr-muted">{item.label}</div>
          <div className="text-sm font-mono text-vr-secondary">{item.value}</div>
        </div>
      ))}
    </div>
  );
}
