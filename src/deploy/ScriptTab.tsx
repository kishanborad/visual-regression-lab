import { DEFAULT_DIFF_SCRIPT } from '../engine/diffScript';

interface Props {
  script: string;
  onChange: (script: string) => void;
}

export default function ScriptTab({ script, onChange }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-vr-border">
        <span className="text-xs text-vr-secondary uppercase tracking-widest">Python Diff Script</span>
        <button
          onClick={() => onChange(DEFAULT_DIFF_SCRIPT)}
          className="btn-secondary text-xs px-2 py-1"
        >
          Reset to Default
        </button>
      </div>
      <textarea
        value={script}
        onChange={(e) => onChange(e.target.value)}
        className="flex-1 w-full bg-vr-deep text-vr-text text-xs font-mono p-4 resize-none focus:outline-none"
        spellCheck={false}
      />
    </div>
  );
}
