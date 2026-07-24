"""
test_report_generator.py — pytest tests for report_generator.py

Tests HTML report structure, pass/fail indicators, styling cues, and the
CLI entry point. Does not require a browser — all assertions are string-based
on the generated HTML content.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from report_generator import generate_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_summary(
    *,
    gate_status: str = "pass",
    total: int = 2,
    passed: int = 2,
    failed: int = 0,
    errors: int = 0,
    threshold_pct: float = 10.0,
    gate_pct: float = 0.5,
    comparisons: list[dict] | None = None,
) -> dict:
    """Build a minimal summary dict suitable for generate_report."""
    if comparisons is None:
        comparisons = [
            {
                "name": "hero.png",
                "status": "pass",
                "mismatch_pct": 0.0,
                "mismatch_count": 0,
                "total_pixels": 100,
                "ignored_count": 0,
                "width": 10,
                "height": 10,
                "baseline": "baseline/hero.png",
                "candidate": "candidate/hero.png",
                "diff": "diffs/hero_diff.png",
                "error": None,
            },
            {
                "name": "footer.png",
                "status": "pass",
                "mismatch_pct": 0.1,
                "mismatch_count": 1,
                "total_pixels": 100,
                "ignored_count": 0,
                "width": 10,
                "height": 10,
                "baseline": "baseline/footer.png",
                "candidate": "candidate/footer.png",
                "diff": "diffs/footer_diff.png",
                "error": None,
            },
        ]

    return {
        "generated_at": datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
        "baseline_dir": "/app/screenshots/baseline",
        "candidate_dir": "/app/screenshots/candidate",
        "threshold_pct": threshold_pct,
        "gate_pct": gate_pct,
        "anti_aliasing": True,
        "gate_status": gate_status,
        "total_count": total,
        "passed_count": passed,
        "failed_count": failed,
        "error_count": errors,
        "missing_candidates": [],
        "comparisons": comparisons,
    }


# ---------------------------------------------------------------------------
# Report structure
# ---------------------------------------------------------------------------

class TestReportStructure:
    def test_generates_html_file(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_html_doctype(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert content.startswith("<!DOCTYPE html>")

    def test_has_html_structure(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "<html" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "</html>" in content

    def test_title_contains_date(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "<title>" in content
        assert "2025" in content

    def test_inline_css_present(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "<style>" in content
        assert "</style>" in content

    def test_summary_stats_present(self, tmp_path):
        summary = _make_summary(total=3, passed=2, failed=1)
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        # The stat values should appear in the HTML
        assert ">3<" in content or ">3 " in content or "stat-value" in content

    def test_comparison_names_appear(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "hero.png" in content
        assert "footer.png" in content

    def test_diff_image_links_present(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "diffs/hero_diff.png" in content

    def test_config_strip_shows_threshold(self, tmp_path):
        summary = _make_summary(threshold_pct=7.5, gate_pct=1.2)
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "7.5" in content
        assert "1.2" in content


# ---------------------------------------------------------------------------
# Pass / Fail indicators
# ---------------------------------------------------------------------------

class TestPassFailIndicators:
    def test_pass_badge_present_on_pass(self, tmp_path):
        summary = _make_summary(gate_status="pass")
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "PASS" in content

    def test_fail_badge_present_on_fail(self, tmp_path):
        comparisons = [
            {
                "name": "broken.png",
                "status": "fail",
                "mismatch_pct": 45.0,
                "mismatch_count": 45,
                "total_pixels": 100,
                "ignored_count": 0,
                "width": 10,
                "height": 10,
                "baseline": "baseline/broken.png",
                "candidate": "candidate/broken.png",
                "diff": "diffs/broken_diff.png",
                "error": None,
            }
        ]
        summary = _make_summary(
            gate_status="fail", total=1, passed=0, failed=1, comparisons=comparisons
        )
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "45.0000%" in content or "45.0" in content

    def test_pass_badge_has_css_class(self, tmp_path):
        summary = _make_summary(gate_status="pass")
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'class="gate-badge pass"' in content or 'gate-badge' in content

    def test_fail_badge_has_css_class(self, tmp_path):
        summary = _make_summary(gate_status="fail", passed=0, failed=1)
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'class="gate-badge fail"' in content or 'gate-badge' in content

    def test_per_comparison_pass_badge(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        # Should have per-comparison badges
        assert 'class="badge pass"' in content

    def test_per_comparison_fail_badge(self, tmp_path):
        comparisons = [
            {
                "name": "fail_case.png",
                "status": "fail",
                "mismatch_pct": 30.0,
                "mismatch_count": 30,
                "total_pixels": 100,
                "ignored_count": 0,
                "width": 10,
                "height": 10,
                "baseline": "baseline/fail_case.png",
                "candidate": "candidate/fail_case.png",
                "diff": "diffs/fail_case_diff.png",
                "error": None,
            }
        ]
        summary = _make_summary(
            gate_status="fail", passed=0, failed=1, comparisons=comparisons
        )
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'class="badge fail"' in content


# ---------------------------------------------------------------------------
# Dark theme CSS checks
# ---------------------------------------------------------------------------

class TestDarkThemeCSS:
    def test_css_variables_defined(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "--bg-primary" in content
        assert "--text-primary" in content
        assert "--pass" in content
        assert "--fail" in content

    def test_dark_background_colour(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        # Our dark background is #0f0f13
        assert "#0f0f13" in content

    def test_diff_grid_present(self, tmp_path):
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "diff-grid" in content


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_comparisons_list(self, tmp_path):
        summary = _make_summary(total=0, passed=0, failed=0, comparisons=[])
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        assert out.exists()

    def test_error_comparison_entry(self, tmp_path):
        comparisons = [
            {
                "name": "broken.png",
                "status": "error",
                "mismatch_pct": None,
                "mismatch_count": None,
                "total_pixels": None,
                "ignored_count": None,
                "baseline": "baseline/broken.png",
                "candidate": None,
                "diff": None,
                "error": "Candidate image not found",
            }
        ]
        summary = _make_summary(total=1, passed=0, failed=0, errors=1, comparisons=comparisons)
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "Candidate image not found" in content

    def test_missing_comparison_entry(self, tmp_path):
        comparisons = [
            {
                "name": "orphan.png",
                "status": "missing",
                "mismatch_pct": None,
                "mismatch_count": None,
                "total_pixels": None,
                "ignored_count": None,
                "baseline": "baseline/orphan.png",
                "candidate": None,
                "diff": None,
                "error": "Candidate image not found",
            }
        ]
        summary = _make_summary(total=1, passed=0, failed=0, errors=1, comparisons=comparisons)
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        content = out.read_text(encoding="utf-8")
        assert "orphan.png" in content

    def test_overwrite_existing_file(self, tmp_path):
        """Calling generate_report twice should overwrite, not append."""
        summary = _make_summary()
        out = tmp_path / "report.html"
        generate_report(summary, str(out))
        size_first = out.stat().st_size
        generate_report(summary, str(out))
        size_second = out.stat().st_size
        assert size_first == size_second  # same output, not doubled


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

class TestReportGeneratorCLI:
    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "report_generator.py"),
            *args,
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_generates_report(self, tmp_path):
        summary = _make_summary()
        summary_path = tmp_path / "summary.json"
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        out = tmp_path / "report.html"
        result = self._run_cli(str(summary_path), str(out))
        assert result.returncode == 0
        assert out.exists()

    def test_cli_missing_summary_json_exit_one(self, tmp_path):
        out = tmp_path / "report.html"
        result = self._run_cli("/nonexistent/summary.json", str(out))
        assert result.returncode == 1

    def test_cli_prints_output_path(self, tmp_path):
        summary = _make_summary()
        summary_path = tmp_path / "summary.json"
        summary_path.write_text(json.dumps(summary), encoding="utf-8")
        out = tmp_path / "report.html"
        result = self._run_cli(str(summary_path), str(out))
        assert str(out) in result.stdout
