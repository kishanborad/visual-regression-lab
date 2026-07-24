"""
batch_compare.py — Batch visual regression runner.

Walks a directory of baseline images, finds matching candidates, runs
diff_engine.compare_image_files on each pair, and writes a summary JSON +
styled HTML report.

Usage
-----
    python batch_compare.py \\
        --baseline-dir screenshots/baseline \\
        --candidate-dir screenshots/candidate \\
        --output-dir reports/ \\
        --threshold 10 \\
        --gate 0.5

All baseline images are matched to a candidate with the same filename.
Candidates that have no matching baseline are listed as warnings.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from diff_engine import compare_image_files
from report_generator import generate_report

# Supported image extensions (case-insensitive)
IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Directory walking
# ---------------------------------------------------------------------------

def find_baseline_images(baseline_dir: Path) -> list[Path]:
    """Return a sorted list of image files under *baseline_dir*."""
    images: list[Path] = []
    for path in sorted(baseline_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path)
    return images


def match_candidate(baseline_path: Path, baseline_dir: Path, candidate_dir: Path) -> Optional[Path]:
    """Return the candidate path corresponding to *baseline_path*, or None."""
    rel = baseline_path.relative_to(baseline_dir)
    candidate = candidate_dir / rel
    if candidate.exists():
        return candidate
    # Try matching with different extension
    stem = candidate.stem
    parent = candidate.parent
    for ext in IMAGE_EXTENSIONS:
        alt = parent / f"{stem}{ext}"
        if alt.exists():
            return alt
    return None


# ---------------------------------------------------------------------------
# Core batch runner
# ---------------------------------------------------------------------------

def run_batch(
    baseline_dir: Path,
    candidate_dir: Path,
    output_dir: Path,
    threshold_pct: float = 10.0,
    gate_pct: float = 0.5,
    anti_aliasing: bool = True,
    diff_color: tuple[int, int, int] = (255, 0, 0),
    diff_alpha_pct: float = 80.0,
    copy_images: bool = True,
) -> dict:
    """Run visual regression comparison on all image pairs.

    Parameters
    ----------
    baseline_dir:
        Directory containing baseline (reference) images.
    candidate_dir:
        Directory containing candidate (new) images.
    output_dir:
        Directory where diff images, summary JSON, and HTML report will be saved.
    threshold_pct:
        Per-pixel colour distance threshold (percentage of max distance).
        A pixel is a mismatch when its distance exceeds this value.
    gate_pct:
        Overall mismatch percentage gate. A comparison *fails* when its
        mismatch_pct exceeds gate_pct.
    anti_aliasing:
        Enable anti-aliasing artifact filtering.
    diff_color:
        RGB tuple for mismatch pixel highlight.
    diff_alpha_pct:
        Opacity of the diff highlight (0–100).
    copy_images:
        Copy baseline and candidate images into output_dir for self-contained
        HTML reports.

    Returns
    -------
    dict
        Summary dict including per-comparison results and aggregate statistics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    diffs_dir = output_dir / "diffs"
    diffs_dir.mkdir(exist_ok=True)

    if copy_images:
        (output_dir / "baseline").mkdir(exist_ok=True)
        (output_dir / "candidate").mkdir(exist_ok=True)

    baseline_images = find_baseline_images(baseline_dir)
    if not baseline_images:
        log.warning("No baseline images found in %s", baseline_dir)

    results: list[dict] = []
    missing_candidates: list[str] = []

    for baseline_path in baseline_images:
        rel = str(baseline_path.relative_to(baseline_dir))
        candidate_path = match_candidate(baseline_path, baseline_dir, candidate_dir)

        if candidate_path is None:
            log.warning("No candidate for baseline: %s", rel)
            missing_candidates.append(rel)
            results.append({
                "name": rel,
                "status": "missing",
                "mismatch_pct": None,
                "mismatch_count": None,
                "total_pixels": None,
                "ignored_count": None,
                "baseline": str(baseline_path),
                "candidate": None,
                "diff": None,
                "error": "Candidate image not found",
            })
            continue

        diff_filename = Path(rel).stem + "_diff.png"
        diff_path = diffs_dir / diff_filename

        try:
            comparison = compare_image_files(
                baseline_path=baseline_path,
                candidate_path=candidate_path,
                threshold_pct=threshold_pct,
                anti_aliasing=anti_aliasing,
                diff_color=diff_color,
                diff_alpha_pct=diff_alpha_pct,
                output_path=diff_path,
            )
        except (ValueError, OSError) as exc:
            log.error("Error comparing %s: %s", rel, exc)
            results.append({
                "name": rel,
                "status": "error",
                "mismatch_pct": None,
                "mismatch_count": None,
                "total_pixels": None,
                "ignored_count": None,
                "baseline": str(baseline_path),
                "candidate": str(candidate_path),
                "diff": None,
                "error": str(exc),
            })
            continue

        # Determine gate status
        gate_status = "pass" if comparison["mismatch_pct"] <= gate_pct else "fail"

        # Paths relative to output_dir for the HTML report
        rel_baseline: Optional[str] = None
        rel_candidate: Optional[str] = None
        if copy_images:
            dest_base = output_dir / "baseline" / Path(rel).name
            dest_cand = output_dir / "candidate" / Path(rel).name
            shutil.copy2(baseline_path, dest_base)
            shutil.copy2(candidate_path, dest_cand)
            rel_baseline = f"baseline/{Path(rel).name}"
            rel_candidate = f"candidate/{Path(rel).name}"

        results.append({
            "name": rel,
            "status": gate_status,
            "mismatch_pct": comparison["mismatch_pct"],
            "mismatch_count": comparison["mismatch_count"],
            "total_pixels": comparison["total_pixels"],
            "ignored_count": comparison["ignored_count"],
            "width": comparison["width"],
            "height": comparison["height"],
            "baseline": rel_baseline or str(baseline_path),
            "candidate": rel_candidate or str(candidate_path),
            "diff": f"diffs/{diff_filename}",
            "error": None,
        })

        status_sym = "✓" if gate_status == "pass" else "✗"
        log.info(
            "%s  %-40s  %6.2f%%  %s",
            status_sym,
            rel,
            comparison["mismatch_pct"],
            gate_status.upper(),
        )

    # Aggregate statistics
    valid = [r for r in results if r["status"] in ("pass", "fail")]
    passed = [r for r in valid if r["status"] == "pass"]
    failed = [r for r in valid if r["status"] == "fail"]
    errors = [r for r in results if r["status"] in ("error", "missing")]

    overall_gate = "pass" if not failed and not errors else "fail"

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "threshold_pct": threshold_pct,
        "gate_pct": gate_pct,
        "anti_aliasing": anti_aliasing,
        "gate_status": overall_gate,
        "total_count": len(results),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "error_count": len(errors),
        "missing_candidates": missing_candidates,
        "comparisons": results,
    }

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batch_compare",
        description=(
            "Batch visual regression runner.\n\n"
            "Compares all baseline images against matching candidates and "
            "generates a JSON summary and an HTML report."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python batch_compare.py \\\n"
            "      --baseline-dir screenshots/baseline \\\n"
            "      --candidate-dir screenshots/candidate \\\n"
            "      --output-dir reports/ --threshold 10 --gate 0.5\n"
        ),
    )
    parser.add_argument("--baseline-dir", required=True, help="Directory of baseline images")
    parser.add_argument("--candidate-dir", required=True, help="Directory of candidate images")
    parser.add_argument("--output-dir", default="reports", help="Output directory for results")
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        metavar="PCT",
        help="Per-pixel colour distance threshold (default: 10.0)",
    )
    parser.add_argument(
        "--gate",
        type=float,
        default=0.5,
        metavar="PCT",
        help="Overall mismatch gate: fail when mismatch_pct > gate (default: 0.5)",
    )
    parser.add_argument(
        "--no-anti-aliasing",
        dest="anti_aliasing",
        action="store_false",
        default=True,
        help="Disable anti-aliasing artifact filtering",
    )
    parser.add_argument(
        "--diff-color",
        metavar="R,G,B",
        default="255,0,0",
        help="Highlight colour for diff pixels (default: 255,0,0)",
    )
    parser.add_argument(
        "--no-copy-images",
        dest="copy_images",
        action="store_false",
        default=True,
        help="Do not copy baseline/candidate into the output directory",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-comparison log output",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point. Exits 0 on gate pass, 1 on gate fail."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )

    try:
        diff_r, diff_g, diff_b = (int(c.strip()) for c in args.diff_color.split(","))
    except ValueError:
        print(f"ERROR: --diff-color must be R,G,B, got: {args.diff_color}", file=sys.stderr)
        return 1

    baseline_dir = Path(args.baseline_dir)
    candidate_dir = Path(args.candidate_dir)
    output_dir = Path(args.output_dir)

    if not baseline_dir.exists():
        print(f"ERROR: baseline-dir does not exist: {baseline_dir}", file=sys.stderr)
        return 1
    if not candidate_dir.exists():
        print(f"ERROR: candidate-dir does not exist: {candidate_dir}", file=sys.stderr)
        return 1

    summary = run_batch(
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        output_dir=output_dir,
        threshold_pct=args.threshold,
        gate_pct=args.gate,
        anti_aliasing=args.anti_aliasing,
        diff_color=(diff_r, diff_g, diff_b),
        copy_images=args.copy_images,
    )

    # Write summary JSON
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    log.info("Summary written to %s", summary_path)

    # Write HTML report
    report_path = output_dir / "report.html"
    generate_report(summary, str(report_path))
    log.info("Report written to %s", report_path)

    # Print final status
    gate_label = "PASS" if summary["gate_status"] == "pass" else "FAIL"
    print(
        f"\n[{gate_label}] {summary['passed_count']}/{summary['total_count']} "
        f"comparisons passed (gate: {args.gate}%)"
    )
    print(f"  Report: {report_path}")

    return 0 if summary["gate_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
