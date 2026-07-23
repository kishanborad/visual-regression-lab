import { useState, useRef, useCallback } from 'react';
import html2canvas from 'html2canvas';
import type { DiffConfig, DiffResult, GateStatus, IgnoreRegion, StatsData } from './types';
import { DEFAULT_CONFIG } from './types';
import { runDiff } from './engine/diffEngine';
import { evaluateGate } from './engine/gateLogic';
import ScenarioFrame from './scenarios/ScenarioFrame';
import BaselinePanel from './canvas/BaselinePanel';
import CandidatePanel from './canvas/CandidatePanel';
import DiffPanel from './canvas/DiffPanel';
import ControlBar from './controls/ControlBar';
import DropZone from './upload/DropZone';
import { padToMatch } from './upload/imageLoader';

export default function App() {
  const [config, setConfig] = useState<DiffConfig>(DEFAULT_CONFIG);
  const [selectedScenario, setSelectedScenario] = useState('button-shift');
  const [result, setResult] = useState<DiffResult | null>(null);
  const [gateStatus, setGateStatus] = useState<GateStatus>('idle');
  const [ignoreRegions, setIgnoreRegions] = useState<IgnoreRegion[]>([]);
  const [running, setRunning] = useState(false);
  const [drawingEnabled, setDrawingEnabled] = useState(false);
  const [baselineImage, setBaselineImage] = useState<ImageData | null>(null);
  const [candidateImage, setCandidateImage] = useState<ImageData | null>(null);
  const [stats, setStats] = useState<StatsData | null>(null);

  const baselineIframeRef = useRef<HTMLIFrameElement>(null);
  const candidateIframeRef = useRef<HTMLIFrameElement>(null);

  const isCustom = selectedScenario === 'custom';

  const captureIframe = async (iframe: HTMLIFrameElement): Promise<ImageData> => {
    const doc = iframe.contentDocument;
    if (!doc?.body) throw new Error('Cannot access iframe document');
    const canvas = await html2canvas(doc.body, {
      width: iframe.clientWidth,
      height: iframe.clientHeight,
      useCORS: true,
      backgroundColor: '#0d0d1a',
    });
    const ctx = canvas.getContext('2d')!;
    return ctx.getImageData(0, 0, canvas.width, canvas.height);
  };

  const handleRunDiff = useCallback(async () => {
    if (running) return;
    setRunning(true);
    setGateStatus('idle');

    try {
      let baseline: ImageData;
      let candidate: ImageData;

      if (isCustom) {
        if (!baselineImage || !candidateImage) {
          setRunning(false);
          return;
        }
        const maxW = Math.max(baselineImage.width, candidateImage.width);
        const maxH = Math.max(baselineImage.height, candidateImage.height);
        baseline = padToMatch(baselineImage, maxW, maxH);
        candidate = padToMatch(candidateImage, maxW, maxH);
      } else {
        const baseIframe = baselineIframeRef.current;
        const candIframe = candidateIframeRef.current;
        if (!baseIframe || !candIframe) { setRunning(false); return; }
        // Wait for iframes to render
        await new Promise((r) => setTimeout(r, 500));
        baseline = await captureIframe(baseIframe);
        candidate = await captureIframe(candIframe);
      }

      setBaselineImage(baseline);
      setCandidateImage(candidate);

      const diffResult = await runDiff(
        baseline.data,
        candidate.data,
        baseline.width,
        baseline.height,
        config,
        ignoreRegions,
      );

      setResult(diffResult);
      const gate = evaluateGate(diffResult.mismatchPercent, config.gateThreshold);
      setGateStatus(gate);
      setStats({
        totalPixels: diffResult.totalPixels,
        mismatchCount: diffResult.mismatchCount,
        mismatchPercent: diffResult.mismatchPercent,
        width: diffResult.width,
        height: diffResult.height,
        ignoredCount: diffResult.ignoredCount,
      });
    } catch (err) {
      console.error('Diff failed:', err);
    } finally {
      setRunning(false);
    }
  }, [running, isCustom, baselineImage, candidateImage, config, ignoreRegions]);

  return (
    <div className="h-screen flex flex-col bg-vr-bg overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-vr-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-vr-accentDim to-vr-accent flex items-center justify-center shadow-glow">
            <span className="text-white text-sm font-bold">VR</span>
          </div>
          <h1 className="text-lg font-semibold bg-gradient-to-r from-vr-text to-vr-secondary bg-clip-text text-transparent">
            Visual Regression Lab
          </h1>
        </div>
        <span className="text-xs text-vr-muted tracking-wide">
          Pixel-perfect UI comparison powered by Python
        </span>
      </header>

      {/* Control bar */}
      <ControlBar
        config={config}
        onConfigChange={setConfig}
        selectedScenario={selectedScenario}
        onScenarioChange={(id) => {
          setSelectedScenario(id);
          setResult(null);
          setGateStatus('idle');
          setStats(null);
          setIgnoreRegions([]);
          setBaselineImage(null);
          setCandidateImage(null);
        }}
        onRunDiff={handleRunDiff}
        running={running}
        drawingEnabled={drawingEnabled}
        onToggleDrawing={() => setDrawingEnabled(!drawingEnabled)}
        onClearRegions={() => setIgnoreRegions([])}
        gateStatus={gateStatus}
        stats={stats}
      />

      {/* Hidden iframes for preset scenarios */}
      {!isCustom && (
        <div className="absolute -left-[9999px] w-[400px] h-[500px]">
          <ScenarioFrame ref={baselineIframeRef} scenarioId={selectedScenario} version="a" />
          <ScenarioFrame ref={candidateIframeRef} scenarioId={selectedScenario} version="b" />
        </div>
      )}

      {/* Three panels */}
      <div className="flex-1 flex gap-3 px-4 pb-3 min-h-0 mt-3">
        {isCustom && !baselineImage ? (
          <DropZone label="Drop baseline image" onImageLoad={setBaselineImage} />
        ) : (
          <div className="flex-1 glass-panel overflow-hidden">
            <BaselinePanel
              imageData={baselineImage}
              ignoreRegions={ignoreRegions}
              drawingEnabled={drawingEnabled}
              onRegionsChange={setIgnoreRegions}
            />
          </div>
        )}

        {isCustom && !candidateImage ? (
          <DropZone label="Drop candidate image" onImageLoad={setCandidateImage} />
        ) : (
          <div className="flex-1 glass-panel overflow-hidden">
            <CandidatePanel imageData={candidateImage} />
          </div>
        )}

        <div className="flex-1 glass-panel overflow-hidden">
          <DiffPanel diffResult={result} gateStatus={gateStatus} />
        </div>
      </div>
    </div>
  );
}
