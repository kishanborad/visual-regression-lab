import { forwardRef, useEffect } from 'react';

interface Props {
  scenarioId: string;
  version: 'a' | 'b';
}

const ScenarioFrame = forwardRef<HTMLIFrameElement, Props>(({ scenarioId, version }, ref) => {
  const base = import.meta.env.BASE_URL;
  const src = `${base}scenarios.html?scenario=${scenarioId}&version=${version}`;

  useEffect(() => {
    const iframe = (ref as React.RefObject<HTMLIFrameElement>)?.current;
    if (iframe?.contentWindow) {
      iframe.contentWindow.postMessage(
        { type: 'setScenario', scenario: scenarioId, version },
        '*',
      );
    }
  }, [scenarioId, version, ref]);

  return (
    <iframe
      ref={ref}
      src={src}
      title={`Scenario ${version.toUpperCase()}`}
      className="absolute inset-0 w-full h-full border-0"
      sandbox="allow-scripts allow-same-origin"
    />
  );
});

ScenarioFrame.displayName = 'ScenarioFrame';

export default ScenarioFrame;
