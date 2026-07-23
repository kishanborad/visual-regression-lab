# Visual Regression Lab

A browser-based visual regression testing tool. Compare two builds of the same UI pixel by pixel using a Python-powered diff engine (PIL/Pillow via Pyodide). Tune thresholds, draw ignore regions, toggle anti-aliasing, and watch the pass/fail gate evaluate. Auto-generates GitHub Actions workflows and Docker commands. No server, no API keys, runs entirely in the browser.

**Live demo:** [kishanborad.github.io/visual-regression-lab](https://kishanborad.github.io/visual-regression-lab/)

## What it does

Three-panel comparison layout:

- **Baseline** — version A of the UI, captured from a live React component rendered in a hidden iframe
- **Candidate** — version B with a CSS mutation applied (button shifted, color changed, element missing, etc.)
- **Diff** — pixel-by-pixel comparison result from the Python PIL engine, with mismatched pixels highlighted

## Preset scenarios

| Scenario | What changes in Build B | What it teaches |
|----------|------------------------|-----------------|
| Button Shift | Submit button shifts 3px right + 2px down | Layout drift from spacing changes |
| Color Swap | CTA button color changes subtly, header lightens | Color regressions invisible to code review |
| Missing Element | Progress bar disappears | Component removal bugs |
| Font Change | Title font swaps from Poppins 700 to Inter 600 | Typography regressions |
| Spacing Collapse | Section gaps shrink, divider disappears | Margin collapse bugs |

## Controls

- **Threshold slider** — color distance tolerance (0-100%)
- **Anti-aliasing toggle** — skip anti-aliased pixels
- **Diff color picker** — highlight color for mismatches
- **Alpha slider** — diff overlay opacity
- **Ignore regions** — draw rectangles on the baseline to exclude areas
- **Gate threshold** — max allowed mismatch % for pass/fail
- **Custom upload** — drop your own PNG/JPG/WEBP images to compare

## Getting started

```bash
git clone https://github.com/kishanborad/visual-regression-lab.git
cd visual-regression-lab
npm install
npm run dev
```

Open `http://localhost:5173`.

## Scripts

```bash
npm run dev        # Start dev server
npm run build      # Production build
npm run preview    # Preview production build
npm test           # Run unit tests (Vitest)
npm run typecheck  # TypeScript check
npm run deploy     # Deploy to GitHub Pages
```

## Tech stack

- React 18 + TypeScript
- Vite 5 + Tailwind CSS 3
- Python (Pyodide — PIL/Pillow for pixel comparison, loaded from CDN)
- Canvas API (three comparison panels, ignore region overlays)
- html2canvas (iframe DOM to pixel capture)
- GitHub Actions (auto-generated workflow YAML)
- Docker (auto-generated Dockerfile and run commands)
- MediaRecorder API (video recording)
- Vitest (unit tests)
- GitHub Pages (hosting)

## Author

Kishan Borad
- [GitHub](https://github.com/kishanborad)
- [LinkedIn](https://linkedin.com/in/kishanborad27)

## License

MIT — see [LICENSE](LICENSE).
