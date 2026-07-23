let pyodidePromise: Promise<any> | null = null;

export function loadPyodide(): Promise<any> {
  if (pyodidePromise) return pyodidePromise;

  pyodidePromise = (async () => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.0/full/pyodide.js';
    document.head.appendChild(script);

    await new Promise<void>((resolve, reject) => {
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Pyodide'));
    });

    const pyodide = await (globalThis as any).loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.0/full/',
    });

    await pyodide.loadPackage('Pillow');
    return pyodide;
  })();

  return pyodidePromise;
}
