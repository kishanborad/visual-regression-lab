import { useState } from 'react';
import type { DiffConfig } from '../types';
import ScriptTab from './ScriptTab';
import DeployTab from './DeployTab';

interface Props {
  config: DiffConfig;
  diffScript: string;
  onDiffScriptChange: (script: string) => void;
}

export default function BottomTabs({ config, diffScript, onDiffScriptChange }: Props) {
  const [activeTab, setActiveTab] = useState<'script' | 'deploy' | null>(null);

  return (
    <div className="mx-4 mb-3">
      {/* Tab buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => setActiveTab(activeTab === 'script' ? null : 'script')}
          className={`text-xs px-4 py-2 rounded-t-lg transition-all duration-200 ${
            activeTab === 'script'
              ? 'bg-vr-surface text-vr-accent border border-b-0 border-vr-border'
              : 'text-vr-muted hover:text-vr-secondary'
          }`}
        >
          {'</'+'>'} Script
        </button>
        <button
          onClick={() => setActiveTab(activeTab === 'deploy' ? null : 'deploy')}
          className={`text-xs px-4 py-2 rounded-t-lg transition-all duration-200 ${
            activeTab === 'deploy'
              ? 'bg-vr-surface text-vr-accent border border-b-0 border-vr-border'
              : 'text-vr-muted hover:text-vr-secondary'
          }`}
        >
          ▶ Deploy
        </button>
      </div>

      {/* Tab content */}
      {activeTab && (
        <div className="glass-panel rounded-tl-none h-56 overflow-hidden animate-slide-up">
          {activeTab === 'script' ? (
            <ScriptTab script={diffScript} onChange={onDiffScriptChange} />
          ) : (
            <DeployTab config={config} />
          )}
        </div>
      )}
    </div>
  );
}
