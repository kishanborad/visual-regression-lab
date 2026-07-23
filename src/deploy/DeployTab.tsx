import { useState } from 'react';
import type { DiffConfig } from '../types';
import { generateActionsYaml } from './actionsYaml';
import { generateDockerConfig } from './dockerConfig';

interface Props {
  config: DiffConfig;
}

export default function DeployTab({ config }: Props) {
  const [subTab, setSubTab] = useState<'actions' | 'docker'>('actions');
  const [copied, setCopied] = useState(false);

  const yaml = generateActionsYaml(config);
  const { dockerfile, runCommand } = generateDockerConfig(config);
  const content = subTab === 'actions' ? yaml : `# Dockerfile\n${dockerfile}\n# Run command\n${runCommand}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-vr-border">
        <button
          onClick={() => setSubTab('actions')}
          className={`text-xs px-3 py-1 rounded-md transition-all duration-200 ${
            subTab === 'actions'
              ? 'bg-vr-accent/10 text-vr-accent border border-vr-accent/30'
              : 'text-vr-muted hover:text-vr-secondary'
          }`}
        >
          GitHub Actions
        </button>
        <button
          onClick={() => setSubTab('docker')}
          className={`text-xs px-3 py-1 rounded-md transition-all duration-200 ${
            subTab === 'docker'
              ? 'bg-vr-accent/10 text-vr-accent border border-vr-accent/30'
              : 'text-vr-muted hover:text-vr-secondary'
          }`}
        >
          Docker
        </button>
        <button onClick={handleCopy} className="btn-secondary text-xs px-3 py-1 ml-auto">
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      <pre className="flex-1 overflow-auto p-4 text-xs font-mono text-vr-secondary bg-vr-deep">
        {content}
      </pre>
    </div>
  );
}
