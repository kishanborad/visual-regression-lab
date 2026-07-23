import { useState } from 'react';
import type { DiffConfig, DiffResult, GateStatus, IgnoreRegion } from './types';
import { DEFAULT_CONFIG } from './types';

export default function App() {
  const [_config, _setConfig] = useState<DiffConfig>(DEFAULT_CONFIG);
  const [_selectedScenario, _setSelectedScenario] = useState('button-shift');
  const [_result, _setResult] = useState<DiffResult | null>(null);
  const [_gateStatus, _setGateStatus] = useState<GateStatus>('idle');
  const [_ignoreRegions, _setIgnoreRegions] = useState<IgnoreRegion[]>([]);
  const [_running, _setRunning] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-vr-bg overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-vr-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-vr-accentDim to-vr-accent flex items-center justify-center">
            <span className="text-white text-sm font-bold">VR</span>
          </div>
          <h1 className="text-lg font-semibold bg-gradient-to-r from-vr-text to-vr-secondary bg-clip-text text-transparent">
            Visual Regression Lab
          </h1>
        </div>
        <span className="text-xs text-vr-muted tracking-wide">
          Pixel-perfect UI comparison
        </span>
      </header>

      {/* Control bar placeholder */}
      <div className="glass-panel mx-4 mt-4 p-4">
        <p className="text-vr-secondary text-sm">Controls will render here</p>
      </div>

      {/* Three panels placeholder */}
      <div className="flex-1 flex gap-4 p-4 min-h-0">
        <div className="flex-1 glass-panel flex items-center justify-center">
          <span className="text-vr-muted text-sm">Baseline</span>
        </div>
        <div className="flex-1 glass-panel flex items-center justify-center">
          <span className="text-vr-muted text-sm">Candidate</span>
        </div>
        <div className="flex-1 glass-panel flex items-center justify-center">
          <span className="text-vr-muted text-sm">Diff</span>
        </div>
      </div>

      {/* Bottom tabs placeholder */}
      <div className="glass-panel mx-4 mb-4 p-3">
        <p className="text-vr-secondary text-sm">Bottom tabs will render here</p>
      </div>
    </div>
  );
}
