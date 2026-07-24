"""
diff_engine.py — PIL-based pixel-level image comparison engine.

Standalone module for visual regression testing. Can be used:
  - Directly via CLI: python diff_engine.py baseline.png candidate.png
  - As a Python module: from diff_engine import compare_images
  - Loaded by Pyodide in the browser (same API, buffer-based variant)

Dependencies: Pillow >= 10.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from PIL import Image


# ---------------------------------------------------------------------------
# Core comparison API
# ---------------------------------------------------------------------------

MAX_COLOR_DISTANCE: float = 441.6729559300637  # sqrt(255² × 3), exact value


def compare_images(
    baseline_bytes: bytes,
    candidate_bytes: bytes,
    width: int,
    height: int,
    threshold_pct: float,
    anti_aliasing: bool,
    diff_color_r: int,
    diff_color_g: int,
    diff_color_b: int,
    diff_alpha_pct: float,
    ignore_regions: list[tuple[int, int, int, int]],
) -> tuple[bytes, int, int, float, int]:
    """Compare two raw RGBA pixel buffers and return diff image + statistics.

    Parameters
    ----------
    baseline_bytes:
        Raw RGBA bytes for the baseline image (width × height × 4).
    candidate_bytes:
        Raw RGBA bytes for the candidate image (width × height × 4).
    width:
        Image width in pixels. Both images must share the same dimensions.
    height:
        Image height in pixels. Both images must share the same dimensions.
    threshold_pct:
        Color-distance threshold expressed as a percentage of the maximum
        possible distance (0–100). Pixels whose Euclidean RGB distance
        exceeds this value are marked as mismatches.
    anti_aliasing:
        When ``True``, pixels that are surrounded by a majority of matching
        neighbors are treated as anti-aliasing artifacts and not counted as
        mismatches.
    diff_color_r / diff_color_g / diff_color_b:
        Highlight colour (0–255 each) used to paint mismatch pixels in the
        output diff image.
    diff_alpha_pct:
        Opacity of the highlight colour as a percentage (0–100).
    ignore_regions:
        List of ``(x, y, w, h)`` tuples identifying rectangular regions to
        exclude from comparison. Pixels inside these regions are copied from
        the baseline at reduced opacity for visual context.

    Returns
    -------
    result_bytes:
        Raw RGBA bytes for the diff image.
    mismatch_count:
        Total number of pixels that exceeded the threshold (after AA
        filtering and ignoring regions).
    total_pixels:
        Total number of pixels that were actually compared (total − ignored).
    mismatch_pct:
        ``mismatch_count / total_pixels × 100``.
    ignored_count:
        Number of pixels skipped due to ``ignore_regions``.
    """
    if len(baseline_bytes) != width * height * 4:
        raise ValueError(
            f"baseline_bytes length {len(baseline_bytes)} does not match "
            f"{width}×{height}×4 = {width * height * 4}"
        )
    if len(candidate_bytes) != width * height * 4:
        raise ValueError(
            f"candidate_bytes length {len(candidate_bytes)} does not match "
            f"{width}×{height}×4 = {width * height * 4}"
        )

    baseline = Image.frombytes("RGBA", (width, height), baseline_bytes)
    candidate = Image.frombytes("RGBA", (width, height), candidate_bytes)

    base_px = baseline.load()
    cand_px = candidate.load()

    diff_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    diff_px = diff_img.load()

    threshold = (threshold_pct / 100.0) * MAX_COLOR_DISTANCE
    diff_alpha = int((diff_alpha_pct / 100.0) * 255)

    # Build ignore mask from region list
    ignore_mask: set[tuple[int, int]] = set()
    for rx, ry, rw, rh in ignore_regions:
        for iy in range(max(0, ry), min(height, ry + rh)):
            for ix in range(max(0, rx), min(width, rx + rw)):
                ignore_mask.add((ix, iy))

    mismatch_count = 0
    ignored_count = len(ignore_mask)

    for y in range(height):
        for x in range(width):
            if (x, y) in ignore_mask:
                # Show baseline at reduced opacity for context
                br, bg, bb, ba = base_px[x, y]
                diff_px[x, y] = (br, bg, bb, ba // 4)
                continue

            br, bg, bb, ba = base_px[x, y]
            cr, cg, cb, ca = cand_px[x, y]

            dr = br - cr
            dg = bg - cg
            db = bb - cb
            distance = (dr * dr + dg * dg + db * db) ** 0.5

            if distance > threshold:
                if anti_aliasing and _is_antialiased(
                    base_px, cand_px, x, y, width, height, threshold
                ):
                    # Likely an AA artifact — show dimmed but don't count
                    diff_px[x, y] = (br, bg, bb, ba // 4)
                    continue

                mismatch_count += 1
                diff_px[x, y] = (diff_color_r, diff_color_g, diff_color_b, diff_alpha)
            else:
                # Match — copy baseline dimmed for context
                diff_px[x, y] = (br, bg, bb, ba // 4)

    total_pixels = width * height - ignored_count
    mismatch_pct = (mismatch_count / total_pixels * 100) if total_pixels > 0 else 0.0

    result_bytes = diff_img.tobytes()
    return (result_bytes, mismatch_count, total_pixels, mismatch_pct, ignored_count)


def compare_image_files(
    baseline_path: str | Path,
    candidate_path: str | Path,
    threshold_pct: float = 10.0,
    anti_aliasing: bool = True,
    diff_color: tuple[int, int, int] = (255, 0, 0),
    diff_alpha_pct: float = 80.0,
    ignore_regions: Optional[list[tuple[int, int, int, int]]] = None,
    output_path: Optional[str | Path] = None,
) -> dict:
    """High-level helper: compare two image files on disk and return a result dict.

    Parameters
    ----------
    baseline_path:
        Path to the baseline PNG/JPEG image.
    candidate_path:
        Path to the candidate PNG/JPEG image.
    threshold_pct:
        Mismatch threshold as a percentage of max colour distance.
    anti_aliasing:
        Enable anti-aliasing artifact filtering.
    diff_color:
        RGB tuple for mismatch pixel highlight colour.
    diff_alpha_pct:
        Opacity of the diff highlight (0–100).
    ignore_regions:
        List of ``(x, y, w, h)`` rectangles to exclude from comparison.
    output_path:
        If given, save the diff image to this path.

    Returns
    -------
    dict with keys:
        baseline, candidate, width, height, threshold_pct, mismatch_count,
        total_pixels, mismatch_pct, ignored_count, status, output_path
    """
    baseline_path = Path(baseline_path)
    candidate_path = Path(candidate_path)

    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {baseline_path}")
    if not candidate_path.exists():
        raise FileNotFoundError(f"Candidate not found: {candidate_path}")

    base_img = Image.open(baseline_path).convert("RGBA")
    cand_img = Image.open(candidate_path).convert("RGBA")

    if base_img.size != cand_img.size:
        raise ValueError(
            f"Image dimensions do not match: baseline={base_img.size}, "
            f"candidate={cand_img.size}"
        )

    width, height = base_img.size
    r, g, b = diff_color

    diff_bytes, mismatch_count, total_pixels, mismatch_pct, ignored_count = compare_images(
        baseline_bytes=base_img.tobytes(),
        candidate_bytes=cand_img.tobytes(),
        width=width,
        height=height,
        threshold_pct=threshold_pct,
        anti_aliasing=anti_aliasing,
        diff_color_r=r,
        diff_color_g=g,
        diff_color_b=b,
        diff_alpha_pct=diff_alpha_pct,
        ignore_regions=ignore_regions or [],
    )

    saved_path: Optional[str] = None
    if output_path is not None:
        diff_img = Image.frombytes("RGBA", (width, height), diff_bytes)
        diff_img.save(output_path)
        saved_path = str(output_path)

    return {
        "baseline": str(baseline_path),
        "candidate": str(candidate_path),
        "width": width,
        "height": height,
        "threshold_pct": threshold_pct,
        "mismatch_count": mismatch_count,
        "total_pixels": total_pixels,
        "mismatch_pct": round(mismatch_pct, 4),
        "ignored_count": ignored_count,
        "status": "pass" if mismatch_pct <= threshold_pct else "fail",
        "output_path": saved_path,
    }


# ---------------------------------------------------------------------------
# Anti-aliasing detection helper
# ---------------------------------------------------------------------------

def _is_antialiased(
    base_px,
    cand_px,
    x: int,
    y: int,
    w: int,
    h: int,
    threshold: float,
) -> bool:
    """Return True if the differing pixel at (x, y) is likely an AA artifact.

    A pixel is classified as anti-aliased when at least half of its valid
    8-connected neighbours have a colour-distance below the comparison
    threshold in both images.  This heuristic avoids false positives caused
    by sub-pixel rendering differences between browser render engines.

    Parameters
    ----------
    base_px:
        PixelAccess object for the baseline image.
    cand_px:
        PixelAccess object for the candidate image.
    x, y:
        Coordinates of the pixel under inspection.
    w, h:
        Image dimensions (used for bounds checking).
    threshold:
        Absolute colour-distance threshold (already scaled from threshold_pct).
    """
    similar_neighbors = 0
    total_neighbors = 0

    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                total_neighbors += 1
                br, bg, bb, _ = base_px[nx, ny]
                cr, cg, cb, _ = cand_px[nx, ny]
                dr = br - cr
                dg = bg - cg
                db = bb - cb
                distance = (dr * dr + dg * dg + db * db) ** 0.5
                if distance <= threshold:
                    similar_neighbors += 1

    return total_neighbors > 0 and (similar_neighbors / total_neighbors) >= 0.5


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diff_engine",
        description=(
            "PIL-based visual regression pixel comparator.\n\n"
            "Compares two images and outputs a JSON result with mismatch "
            "statistics and optionally saves a diff image highlighting "
            "changed pixels."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python diff_engine.py baseline.png candidate.png\n"
            "  python diff_engine.py baseline.png candidate.png --threshold 5 --diff diff.png\n"
            "  python diff_engine.py baseline.png candidate.png --no-anti-aliasing --gate 1.0"
        ),
    )
    parser.add_argument("baseline", help="Path to the baseline image")
    parser.add_argument("candidate", help="Path to the candidate image")
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        metavar="PCT",
        help="Mismatch threshold as percentage of max colour distance (default: 10.0)",
    )
    parser.add_argument(
        "--gate",
        type=float,
        default=None,
        metavar="PCT",
        help=(
            "Exit with code 1 if mismatch_pct exceeds this value. "
            "Defaults to the same value as --threshold."
        ),
    )
    parser.add_argument(
        "--diff",
        metavar="PATH",
        default=None,
        help="Save the diff image to this path (PNG recommended)",
    )
    parser.add_argument(
        "--diff-color",
        metavar="R,G,B",
        default="255,0,0",
        help="Highlight colour for mismatch pixels as R,G,B (default: 255,0,0)",
    )
    parser.add_argument(
        "--diff-alpha",
        type=float,
        default=80.0,
        metavar="PCT",
        help="Opacity of the diff highlight 0–100 (default: 80.0)",
    )
    parser.add_argument(
        "--no-anti-aliasing",
        dest="anti_aliasing",
        action="store_false",
        default=True,
        help="Disable anti-aliasing artifact filtering",
    )
    parser.add_argument(
        "--ignore",
        metavar="X,Y,W,H",
        action="append",
        default=[],
        help=(
            "Ignore region specified as X,Y,W,H (can be repeated). "
            "Example: --ignore 0,0,100,50"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable summary; only output JSON",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point. Returns exit code (0 = pass, 1 = fail or error)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Parse diff colour
    try:
        diff_r, diff_g, diff_b = (int(c.strip()) for c in args.diff_color.split(","))
    except ValueError:
        print(
            f"ERROR: --diff-color must be R,G,B integers, got: {args.diff_color}",
            file=sys.stderr,
        )
        return 1

    # Parse ignore regions
    ignore_regions: list[tuple[int, int, int, int]] = []
    for region_str in args.ignore:
        try:
            parts = [int(v.strip()) for v in region_str.split(",")]
            if len(parts) != 4:
                raise ValueError
            ignore_regions.append(tuple(parts))  # type: ignore[arg-type]
        except ValueError:
            print(
                f"ERROR: --ignore must be X,Y,W,H integers, got: {region_str}",
                file=sys.stderr,
            )
            return 1

    try:
        result = compare_image_files(
            baseline_path=args.baseline,
            candidate_path=args.candidate,
            threshold_pct=args.threshold,
            anti_aliasing=args.anti_aliasing,
            diff_color=(diff_r, diff_g, diff_b),
            diff_alpha_pct=args.diff_alpha,
            ignore_regions=ignore_regions,
            output_path=args.diff,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Determine gate (default: same as threshold)
    gate = args.gate if args.gate is not None else args.threshold
    passed = result["mismatch_pct"] <= gate

    if not args.quiet:
        status_label = "PASS" if passed else "FAIL"
        print(f"[{status_label}] {result['mismatch_pct']:.4f}% mismatch", file=sys.stderr)
        print(
            f"  Pixels compared: {result['total_pixels']:,}  |  "
            f"Mismatches: {result['mismatch_count']:,}  |  "
            f"Ignored: {result['ignored_count']:,}",
            file=sys.stderr,
        )
        if result["output_path"]:
            print(f"  Diff image saved: {result['output_path']}", file=sys.stderr)

    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
