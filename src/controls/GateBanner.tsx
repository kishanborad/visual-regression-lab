import type { GateStatus } from '../types';

interface Props {
  gateStatus: GateStatus;
  mismatchPercent: number;
  gateThreshold: number;
}

export default function GateBanner({ gateStatus, mismatchPercent, gateThreshold }: Props) {
  if (gateStatus === 'idle') return null;

  const isPass = gateStatus === 'pass';

  return (
    <div
      className={`animate-slide-up flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium ${
        isPass
          ? 'bg-vr-pass/10 border border-vr-pass/30 text-vr-pass shadow-glow-pass'
          : 'bg-vr-fail/10 border border-vr-fail/30 text-vr-fail shadow-glow-fail'
      }`}
    >
      <div className={`w-3 h-3 rounded-full ${isPass ? 'bg-vr-pass animate-pulse-glow' : 'bg-vr-fail'}`} />
      <span>
        {isPass ? 'PASS' : 'FAIL'} — {mismatchPercent.toFixed(2)}% mismatch (gate: {gateThreshold}%)
      </span>
    </div>
  );
}
