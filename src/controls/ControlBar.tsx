import type { DiffConfig, GateStatus, StatsData } from '../types';
import { PRESETS } from '../scenarios/presets';
import ThresholdSlider from './ThresholdSlider';
import AlphaSlider from './AlphaSlider';
import ColorPicker from './ColorPicker';
import GateBanner from './GateBanner';
import StatsRow from './StatsRow';

interface Props {
  config: DiffConfig;
  onConfigChange: (config: DiffConfig) => void;
  selectedScenario: string;
  onScenarioChange: (id: string) => void;
  onRunDiff: () => void;
  running: boolean;
  drawingEnabled: boolean;
  onToggleDrawing: () => void;
  onClearRegions: () => void;
  gateStatus: GateStatus;
  stats: StatsData | null;
}

export default function ControlBar({
  config, onConfigChange, selectedScenario, onScenarioChange,
  onRunDiff, running, drawingEnabled, onToggleDrawing, onClearRegions,
  gateStatus, stats,
}: Props) {
  const update = (partial: Partial<DiffConfig>) => onConfigChange({ ...config, ...partial });

  return (
    <div className="glass-panel mx-4 mt-3 p-4 space-y-3">
      {/* Top row: scenario + controls + run */}
      <div className="flex items-end gap-4 flex-wrap">
        {/* Scenario selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-vr-secondary">Scenario</label>
          <select
            value={selectedScenario}
            onChange={(e) => onScenarioChange(e.target.value)}
            className="input-field w-48"
          >
            {PRESETS.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
            <option value="custom">Custom Upload</option>
          </select>
        </div>

        {/* Threshold */}
        <div className="w-36">
          <ThresholdSlider
            label="Threshold"
            value={config.threshold}
            min={0} max={100} step={1} unit="%"
            onChange={(v) => update({ threshold: v })}
          />
        </div>

        {/* Anti-aliasing toggle */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-vr-secondary">Anti-aliasing</label>
          <button
            onClick={() => update({ antiAliasing: !config.antiAliasing })}
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
              config.antiAliasing ? 'bg-vr-accentDim' : 'bg-vr-border'
            }`}
          >
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${
              config.antiAliasing ? 'left-6' : 'left-1'
            }`} />
          </button>
        </div>

        {/* Diff color */}
        <ColorPicker value={config.diffColor} onChange={(v) => update({ diffColor: v })} />

        {/* Alpha */}
        <div className="w-28">
          <AlphaSlider value={config.diffAlpha} onChange={(v) => update({ diffAlpha: v })} />
        </div>

        {/* Ignore region tools */}
        <div className="flex items-end gap-2">
          <button
            onClick={onToggleDrawing}
            className={`btn-secondary text-xs px-3 py-1.5 ${drawingEnabled ? 'border-vr-accent text-vr-accent shadow-glow' : ''}`}
          >
            {drawingEnabled ? '✎ Drawing...' : '✎ Draw Ignore'}
          </button>
          <button onClick={onClearRegions} className="btn-secondary text-xs px-3 py-1.5">
            Clear All
          </button>
        </div>

        {/* Gate threshold */}
        <div className="flex flex-col gap-1">
          <label className="text-xs text-vr-secondary">Gate</label>
          <div className="flex items-center gap-1">
            <input
              type="number"
              value={config.gateThreshold}
              onChange={(e) => update({ gateThreshold: parseFloat(e.target.value) || 0 })}
              className="input-field w-16 text-center"
              step={0.1}
              min={0}
              max={100}
            />
            <span className="text-xs text-vr-muted">%</span>
          </div>
        </div>

        {/* Run button */}
        <button onClick={onRunDiff} disabled={running} className="btn-primary ml-auto">
          {running ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Running...
            </span>
          ) : (
            'Run Diff'
          )}
        </button>
      </div>

      {/* Gate banner */}
      <GateBanner
        gateStatus={gateStatus}
        mismatchPercent={stats?.mismatchPercent ?? 0}
        gateThreshold={config.gateThreshold}
      />

      {/* Stats row */}
      <StatsRow stats={stats} />
    </div>
  );
}
