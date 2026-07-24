"""
test_batch_compare.py — pytest tests for batch_compare.py

Tests directory walking, candidate matching, batch execution, report
generation, and CLI argument parsing. All file I/O uses tmp_path so no
permanent files are created.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from batch_compare import (
    find_baseline_images,
    match_candidate,
    run_batch,
    main as batch_main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_png(path: Path, color: tuple[int, int, int, int] = (128, 128, 128, 255)) -> None:
    Image.new("RGBA", (10, 10), color).save(str(path))


def _populate_dirs(
    baseline_dir: Path,
    candidate_dir: Path,
    names: list[str],
    same: bool = True,
) -> None:
    """Populate baseline and candidate dirs with test images."""
    for name in names:
        _save_png(baseline_dir / name, (200, 200, 200, 255))
        color = (200, 200, 200, 255) if same else (0, 0, 0, 255)
        _save_png(candidate_dir / name, color)


# ---------------------------------------------------------------------------
# find_baseline_images
# ---------------------------------------------------------------------------

class TestFindBaselineImages:
    def test_finds_png_files(self, tmp_path):
        d = tmp_path / "baselines"
        d.mkdir()
        (d / "a.png").touch()
        (d / "b.png").touch()
        (d / "not_image.txt").touch()
        found = find_baseline_images(d)
        names = {p.name for p in found}
        assert "a.png" in names
        assert "b.png" in names
        assert "not_image.txt" not in names

    def test_empty_directory_returns_empty(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        assert find_baseline_images(d) == []

    def test_recurses_subdirectories(self, tmp_path):
        d = tmp_path / "baselines"
        sub = d / "sub"
        sub.mkdir(parents=True)
        _save_png(d / "top.png")
        _save_png(sub / "nested.png")
        found = find_baseline_images(d)
        names = {p.name for p in found}
        assert "top.png" in names
        assert "nested.png" in names

    def test_supports_jpg_extension(self, tmp_path):
        d = tmp_path / "baselines"
        d.mkdir()
        # Create a valid JPEG
        img = Image.new("RGB", (5, 5), (100, 100, 100))
        img.save(str(d / "photo.jpg"), format="JPEG")
        found = find_baseline_images(d)
        assert any(p.name == "photo.jpg" for p in found)

    def test_sorted_output(self, tmp_path):
        d = tmp_path / "baselines"
        d.mkdir()
        for name in ["c.png", "a.png", "b.png"]:
            _save_png(d / name)
        found = find_baseline_images(d)
        names = [p.name for p in found]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# match_candidate
# ---------------------------------------------------------------------------

class TestMatchCandidate:
    def test_finds_exact_match(self, tmp_path):
        baseline_dir = tmp_path / "baseline"
        candidate_dir = tmp_path / "candidate"
        baseline_dir.mkdir()
        candidate_dir.mkdir()
        baseline = baseline_dir / "hero.png"
        _save_png(baseline)
        _save_png(candidate_dir / "hero.png")
        result = match_candidate(baseline, baseline_dir, candidate_dir)
        assert result is not None
        assert result.name == "hero.png"

    def test_returns_none_when_missing(self, tmp_path):
        baseline_dir = tmp_path / "baseline"
        candidate_dir = tmp_path / "candidate"
        baseline_dir.mkdir()
        candidate_dir.mkdir()
        baseline = baseline_dir / "missing.png"
        _save_png(baseline)
        result = match_candidate(baseline, baseline_dir, candidate_dir)
        assert result is None

    def test_matches_nested_path(self, tmp_path):
        baseline_dir = tmp_path / "baseline"
        candidate_dir = tmp_path / "candidate"
        sub_b = baseline_dir / "flows"
        sub_c = candidate_dir / "flows"
        sub_b.mkdir(parents=True)
        sub_c.mkdir(parents=True)
        _save_png(sub_b / "checkout.png")
        _save_png(sub_c / "checkout.png")
        result = match_candidate(sub_b / "checkout.png", baseline_dir, candidate_dir)
        assert result is not None


# ---------------------------------------------------------------------------
# run_batch
# ---------------------------------------------------------------------------

class TestRunBatch:
    def test_identical_images_all_pass(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["screen1.png", "screen2.png"], same=True)
        summary = run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
        )
        assert summary["gate_status"] == "pass"
        assert summary["passed_count"] == 2
        assert summary["failed_count"] == 0

    def test_different_images_all_fail(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["screen1.png"], same=False)
        summary = run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
        )
        assert summary["gate_status"] == "fail"
        assert summary["failed_count"] == 1

    def test_missing_candidate_recorded(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _save_png(b / "orphan.png")
        # No matching candidate
        summary = run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
        )
        assert "orphan.png" in summary["missing_candidates"]
        assert summary["error_count"] >= 1

    def test_summary_json_written(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["img.png"], same=True)
        # run_batch does not write json; batch CLI does — confirm keys are present
        summary = run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
        )
        required_keys = {
            "gate_status", "total_count", "passed_count", "failed_count",
            "threshold_pct", "gate_pct", "comparisons", "generated_at",
        }
        assert required_keys.issubset(summary.keys())

    def test_diff_images_created(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["view.png"], same=False)
        run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
        )
        diffs = list((o / "diffs").glob("*_diff.png"))
        assert len(diffs) == 1

    def test_copy_images_creates_directories(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["hero.png"], same=True)
        run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
            copy_images=True,
        )
        assert (o / "baseline" / "hero.png").exists()
        assert (o / "candidate" / "hero.png").exists()

    def test_no_copy_images_skips_directories(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["hero.png"], same=True)
        run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
            copy_images=False,
        )
        assert not (o / "baseline").exists()

    def test_empty_baseline_dir(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        summary = run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5,
        )
        assert summary["total_count"] == 0
        assert summary["gate_status"] == "pass"

    def test_gate_pct_boundary(self, tmp_path):
        """Images with 50% mismatch should fail a 0.5% gate."""
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        # Half the pixels changed
        base_img = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        cand_img = base_img.copy()
        px = cand_img.load()
        for y in range(10):
            for x in range(5):
                px[x, y] = (0, 0, 0, 255)
        base_img.save(str(b / "half.png"))
        cand_img.save(str(c / "half.png"))
        summary = run_batch(
            baseline_dir=b, candidate_dir=c, output_dir=o,
            threshold_pct=10.0, gate_pct=0.5, anti_aliasing=False,
        )
        assert summary["failed_count"] == 1
        assert summary["gate_status"] == "fail"


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestBatchCLI:
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "batch_compare.py"),
            *args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_pass_exit_zero(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["a.png"], same=True)
        result = self._run_cli(
            "--baseline-dir", str(b),
            "--candidate-dir", str(c),
            "--output-dir", str(o),
            "--threshold", "10",
            "--gate", "0.5",
            "--quiet",
        )
        assert result.returncode == 0

    def test_cli_fail_exit_one(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["a.png"], same=False)
        result = self._run_cli(
            "--baseline-dir", str(b),
            "--candidate-dir", str(c),
            "--output-dir", str(o),
            "--threshold", "10",
            "--gate", "0.5",
            "--quiet",
            "--no-anti-aliasing",
        )
        assert result.returncode == 1

    def test_cli_missing_baseline_dir_exit_one(self, tmp_path):
        result = self._run_cli(
            "--baseline-dir", "/nonexistent/dir",
            "--candidate-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
        )
        assert result.returncode == 1

    def test_cli_writes_report_html(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["img.png"], same=True)
        self._run_cli(
            "--baseline-dir", str(b),
            "--candidate-dir", str(c),
            "--output-dir", str(o),
            "--quiet",
        )
        assert (o / "report.html").exists()
        assert (o / "summary.json").exists()

    def test_cli_writes_valid_summary_json(self, tmp_path):
        b = tmp_path / "baseline"
        c = tmp_path / "candidate"
        o = tmp_path / "output"
        b.mkdir(); c.mkdir(); o.mkdir()
        _populate_dirs(b, c, ["x.png"], same=True)
        self._run_cli(
            "--baseline-dir", str(b),
            "--candidate-dir", str(c),
            "--output-dir", str(o),
            "--quiet",
        )
        with open(o / "summary.json") as fh:
            data = json.load(fh)
        assert "gate_status" in data
        assert "comparisons" in data
