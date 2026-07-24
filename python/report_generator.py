"""
report_generator.py — Styled HTML report generator for visual regression results.

Takes the summary dict produced by batch_compare.run_batch() and renders a
self-contained HTML file with an inline dark-theme stylesheet. No external
assets are required — images are referenced by relative path so the whole
output directory can be opened directly in a browser.

Usage
-----
    from report_generator import generate_report

    # summary is the dict returned by batch_compare.run_batch()
    generate_report(summary, "reports/report.html")

    # Or run standalone:
    python report_generator.py reports/summary.json reports/report.html
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Inline CSS — dark theme matching the Vite/React frontend palette
# ---------------------------------------------------------------------------

_CSS = """
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --bg-primary:    #0f0f13;
  --bg-secondary:  #1a1a24;
  --bg-card:       #22222f;
  --bg-hover:      #2a2a3a;
  --border:        #333348;
  --text-primary:  #e8e8f0;
  --text-secondary:#9090a8;
  --text-muted:    #5a5a70;
  --accent:        #7c6fcd;
  --accent-glow:   rgba(124,111,205,0.3);
  --pass:          #22c55e;
  --fail:          #ef4444;
  --warn:          #f59e0b;
  --pass-bg:       rgba(34,197,94,0.12);
  --fail-bg:       rgba(239,68,68,0.12);
  --warn-bg:       rgba(245,158,11,0.12);
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Header ─────────────────────────────────────────────────────────────── */
.header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: 24px 32px;
}

.header h1 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}

.header .subtitle {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 4px;
}

/* ── Summary bar ─────────────────────────────────────────────────────────── */
.summary-bar {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
  align-items: center;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.stat-value.pass  { color: var(--pass); }
.stat-value.fail  { color: var(--fail); }
.stat-value.warn  { color: var(--warn); }
.stat-value.total { color: var(--text-primary); }

.gate-badge {
  margin-left: auto;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.gate-badge.pass {
  background: var(--pass-bg);
  color: var(--pass);
  border: 1px solid rgba(34,197,94,0.3);
}

.gate-badge.fail {
  background: var(--fail-bg);
  color: var(--fail);
  border: 1px solid rgba(239,68,68,0.3);
}

/* ── Config strip ────────────────────────────────────────────────────────── */
.config-strip {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border);
  padding: 10px 32px;
  display: flex;
  gap: 24px;
  font-size: 12px;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.config-strip span { white-space: nowrap; }
.config-strip strong { color: var(--text-primary); }

/* ── Summary table ───────────────────────────────────────────────────────── */
.main {
  padding: 24px 32px;
  max-width: 1600px;
  margin: 0 auto;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 40px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead th {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}

tbody tr:last-child { border-bottom: none; }

tbody tr:hover { background: var(--bg-hover); }

tbody td {
  padding: 12px 16px;
  vertical-align: middle;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.badge.pass  { background: var(--pass-bg);  color: var(--pass);  border: 1px solid rgba(34,197,94,0.3); }
.badge.fail  { background: var(--fail-bg);  color: var(--fail);  border: 1px solid rgba(239,68,68,0.3); }
.badge.error { background: var(--warn-bg);  color: var(--warn);  border: 1px solid rgba(245,158,11,0.3); }
.badge.missing { background: var(--warn-bg); color: var(--warn); border: 1px solid rgba(245,158,11,0.3); }

.pct { font-variant-numeric: tabular-nums; }
.pct.fail { color: var(--fail); font-weight: 600; }

/* ── Diff grid ───────────────────────────────────────────────────────────── */
.diff-section { margin-top: 8px; }

.diff-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  margin-top: 12px;
}

.diff-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}

.diff-card.fail { border-color: rgba(239,68,68,0.4); }
.diff-card.pass { border-color: rgba(34,197,94,0.2); }

.diff-card-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.diff-card-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-all;
}

.diff-card-pct {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.diff-card-pct.fail { color: var(--fail); }
.diff-card-pct.pass { color: var(--pass); }

.diff-images {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0;
}

.diff-images figure {
  margin: 0;
  border-right: 1px solid var(--border);
}

.diff-images figure:last-child { border-right: none; }

.diff-images figcaption {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  padding: 6px 10px 4px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.diff-images img {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
  background: #000;
}

.diff-card-meta {
  padding: 8px 16px;
  font-size: 11px;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.footer {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 12px;
  border-top: 1px solid var(--border);
  margin-top: 40px;
}
"""


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _status_badge(status: Optional[str]) -> str:
    if status is None:
        return '<span class="badge error">error</span>'
    cls = {
        "pass": "pass",
        "fail": "fail",
        "error": "error",
        "missing": "missing",
    }.get(status, "error")
    return f'<span class="badge {cls}">{status}</span>'


def _pct_cell(mismatch_pct: Optional[float], gate_pct: float) -> str:
    if mismatch_pct is None:
        return '<td class="pct">—</td>'
    cls = "fail" if mismatch_pct > gate_pct else ""
    return f'<td class="pct {cls}">{mismatch_pct:.4f}%</td>'


def _summary_table(comparisons: list[dict], gate_pct: float) -> str:
    rows: list[str] = []
    for c in comparisons:
        name = c.get("name", "unknown")
        status = c.get("status")
        mismatch_pct = c.get("mismatch_pct")
        mismatch_count = c.get("mismatch_count")
        total_pixels = c.get("total_pixels")
        error = c.get("error") or ""

        diff_link = ""
        if c.get("diff"):
            diff_link = f'<a href="{c["diff"]}">diff</a>'

        pixels_info = "—"
        if mismatch_count is not None and total_pixels is not None:
            pixels_info = f"{mismatch_count:,} / {total_pixels:,}"

        rows.append(
            f"""<tr>
            <td style="font-family:monospace;font-size:12px">{name}</td>
            <td>{_status_badge(status)}</td>
            {_pct_cell(mismatch_pct, gate_pct)}
            <td class="pct">{pixels_info}</td>
            <td>{diff_link}</td>
            <td style="color:var(--warn);font-size:12px">{error}</td>
            </tr>"""
        )

    return f"""
<div class="table-wrapper">
<table>
<thead>
  <tr>
    <th>Comparison</th>
    <th>Status</th>
    <th>Mismatch %</th>
    <th>Px Diff / Total</th>
    <th>Diff</th>
    <th>Notes</th>
  </tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</div>
"""


def _diff_cards(comparisons: list[dict], gate_pct: float) -> str:
    cards: list[str] = []
    for c in comparisons:
        if c.get("status") not in ("pass", "fail"):
            continue

        name = c.get("name", "unknown")
        status = c.get("status", "error")
        mismatch_pct = c.get("mismatch_pct", 0)
        baseline = c.get("baseline") or ""
        candidate = c.get("candidate") or ""
        diff = c.get("diff") or ""
        width = c.get("width", "?")
        height = c.get("height", "?")
        total_pixels = c.get("total_pixels", 0)
        mismatch_count = c.get("mismatch_count", 0)

        pct_cls = "fail" if mismatch_pct > gate_pct else "pass"

        def img_tag(src: str, alt: str) -> str:
            if not src:
                return '<div style="height:140px;background:#111;display:flex;align-items:center;justify-content:center;color:#555;font-size:11px">no image</div>'
            return f'<img src="{src}" alt="{alt}" loading="lazy">'

        cards.append(f"""
<div class="diff-card {status}">
  <div class="diff-card-header">
    <span class="diff-card-name">{name}</span>
    <span class="diff-card-pct {pct_cls}">{mismatch_pct:.4f}%</span>
    {_status_badge(status)}
  </div>
  <div class="diff-images">
    <figure>
      <figcaption>Baseline</figcaption>
      {img_tag(baseline, "baseline")}
    </figure>
    <figure>
      <figcaption>Candidate</figcaption>
      {img_tag(candidate, "candidate")}
    </figure>
    <figure>
      <figcaption>Diff</figcaption>
      {img_tag(diff, "diff")}
    </figure>
  </div>
  <div class="diff-card-meta">
    {width}×{height}px &nbsp;·&nbsp;
    {mismatch_count:,} mismatched / {total_pixels:,} total pixels
  </div>
</div>
""")

    if not cards:
        return "<p style='color:var(--text-muted);'>No image comparisons to display.</p>"

    return f'<div class="diff-grid">{"".join(cards)}</div>'


def generate_report(summary: dict, output_path: str) -> None:
    """Render a styled HTML report from *summary* and write it to *output_path*.

    Parameters
    ----------
    summary:
        Summary dict as returned by ``batch_compare.run_batch()``.
    output_path:
        Destination file path for the HTML report.
    """
    gate_status = summary.get("gate_status", "fail")
    total = summary.get("total_count", 0)
    passed = summary.get("passed_count", 0)
    failed = summary.get("failed_count", 0)
    errors = summary.get("error_count", 0)
    threshold_pct = summary.get("threshold_pct", 10.0)
    gate_pct = summary.get("gate_pct", 0.5)
    anti_aliasing = summary.get("anti_aliasing", True)
    generated_at = summary.get("generated_at", datetime.now(timezone.utc).isoformat())
    baseline_dir = summary.get("baseline_dir", "")
    candidate_dir = summary.get("candidate_dir", "")
    comparisons = summary.get("comparisons", [])

    try:
        dt = datetime.fromisoformat(generated_at)
        generated_label = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        generated_label = generated_at

    gate_badge = f'<span class="gate-badge {gate_status}">{"PASS" if gate_status == "pass" else "FAIL"}</span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Visual Regression Report — {generated_label}</title>
<style>
{_CSS}
</style>
</head>
<body>

<header class="header">
  <h1>Visual Regression Report</h1>
  <p class="subtitle">Generated {generated_label}</p>
</header>

<div class="summary-bar">
  <div class="stat">
    <span class="stat-value total">{total}</span>
    <span class="stat-label">Total</span>
  </div>
  <div class="stat">
    <span class="stat-value pass">{passed}</span>
    <span class="stat-label">Passed</span>
  </div>
  <div class="stat">
    <span class="stat-value fail">{failed}</span>
    <span class="stat-label">Failed</span>
  </div>
  <div class="stat">
    <span class="stat-value warn">{errors}</span>
    <span class="stat-label">Errors</span>
  </div>
  {gate_badge}
</div>

<div class="config-strip">
  <span>Threshold: <strong>{threshold_pct}%</strong></span>
  <span>Gate: <strong>{gate_pct}%</strong></span>
  <span>Anti-aliasing: <strong>{"on" if anti_aliasing else "off"}</strong></span>
  <span>Baseline: <strong style="font-family:monospace">{baseline_dir}</strong></span>
  <span>Candidate: <strong style="font-family:monospace">{candidate_dir}</strong></span>
</div>

<main class="main">
  <p class="section-title">Comparison Summary</p>
  {_summary_table(comparisons, gate_pct)}

  <div class="diff-section">
    <p class="section-title">Diff Images</p>
    {_diff_cards(comparisons, gate_pct)}
  </div>
</main>

<footer class="footer">
  Visual Regression Lab &nbsp;·&nbsp; Report generated {generated_label}
</footer>

</body>
</html>
"""

    Path(output_path).write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """CLI: python report_generator.py summary.json report.html"""
    parser = argparse.ArgumentParser(
        prog="report_generator",
        description="Generate an HTML visual regression report from a summary JSON file.",
    )
    parser.add_argument("summary_json", help="Path to summary.json produced by batch_compare")
    parser.add_argument("output_html", help="Destination path for the HTML report")
    args = parser.parse_args(argv)

    summary_path = Path(args.summary_json)
    if not summary_path.exists():
        print(f"ERROR: summary JSON not found: {summary_path}", file=sys.stderr)
        return 1

    with summary_path.open(encoding="utf-8") as fh:
        summary = json.load(fh)

    generate_report(summary, args.output_html)
    print(f"Report written to: {args.output_html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
