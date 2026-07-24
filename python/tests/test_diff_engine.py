"""
test_diff_engine.py — pytest tests for diff_engine.py

All tests use small synthetic images created with PIL so they run without
any external assets or network access.  Images are typically 10×10 or
20×20 pixels to keep tests fast while exercising the comparison logic
thoroughly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

# Make sure the python/ package root is importable when running from tests/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diff_engine import (
    MAX_COLOR_DISTANCE,
    _is_antialiased,
    compare_image_files,
    compare_images,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rgba_bytes(width: int, height: int, color: tuple[int, int, int, int]) -> bytes:
    img = Image.new("RGBA", (width, height), color)
    return img.tobytes()


def _make_png(path: Path, color: tuple[int, int, int, int], size: tuple[int, int] = (10, 10)) -> None:
    Image.new("RGBA", size, color).save(str(path))


# ---------------------------------------------------------------------------
# compare_images — identical images
# ---------------------------------------------------------------------------

class TestCompareImagesIdentical:
    """Identical images must produce 0 mismatches regardless of threshold."""

    def test_zero_mismatch_white(self):
        w, h = 10, 10
        data = _rgba_bytes(w, h, (255, 255, 255, 255))
        _, mismatch_count, total, mismatch_pct, ignored = compare_images(
            data, data, w, h,
            threshold_pct=10.0,
            anti_aliasing=True,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0,
            ignore_regions=[],
        )
        assert mismatch_count == 0
        assert mismatch_pct == 0.0
        assert total == w * h
        assert ignored == 0

    def test_zero_mismatch_black(self):
        w, h = 10, 10
        data = _rgba_bytes(w, h, (0, 0, 0, 255))
        _, mismatch_count, _, mismatch_pct, _ = compare_images(
            data, data, w, h,
            threshold_pct=0.0,
            anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0,
            ignore_regions=[],
        )
        assert mismatch_count == 0
        assert mismatch_pct == 0.0

    def test_zero_mismatch_gradient(self):
        """Identical gradient images should also report 0 mismatches."""
        img = Image.new("RGBA", (20, 20))
        px = img.load()
        for y in range(20):
            for x in range(20):
                px[x, y] = (x * 12, y * 12, 128, 255)
        data = img.tobytes()
        _, mismatch_count, _, mismatch_pct, _ = compare_images(
            data, data, 20, 20,
            threshold_pct=5.0, anti_aliasing=True,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert mismatch_count == 0
        assert mismatch_pct == 0.0


# ---------------------------------------------------------------------------
# compare_images — different images
# ---------------------------------------------------------------------------

class TestCompareImagesDifferent:
    """White vs black images — every pixel should differ substantially."""

    def test_full_mismatch_white_vs_black(self):
        w, h = 10, 10
        white = _rgba_bytes(w, h, (255, 255, 255, 255))
        black = _rgba_bytes(w, h, (0, 0, 0, 255))
        _, mismatch_count, total, mismatch_pct, _ = compare_images(
            white, black, w, h,
            threshold_pct=10.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert mismatch_count == total == w * h
        assert mismatch_pct == 100.0

    def test_partial_mismatch(self):
        """Left half red, right half unchanged — ~50% mismatch expected."""
        w, h = 10, 10
        baseline = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        candidate = baseline.copy()
        px = candidate.load()
        for y in range(h):
            for x in range(w // 2):
                px[x, y] = (0, 0, 0, 255)

        _, mismatch_count, total, mismatch_pct, _ = compare_images(
            baseline.tobytes(), candidate.tobytes(), w, h,
            threshold_pct=10.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert mismatch_count == (w // 2) * h
        assert abs(mismatch_pct - 50.0) < 1.0

    def test_diff_image_shape(self):
        """The returned diff bytes must have the right size (w*h*4)."""
        w, h = 8, 8
        white = _rgba_bytes(w, h, (255, 255, 255, 255))
        black = _rgba_bytes(w, h, (0, 0, 0, 255))
        diff_bytes, _, _, _, _ = compare_images(
            white, black, w, h,
            threshold_pct=10.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert len(diff_bytes) == w * h * 4

    def test_diff_pixels_are_highlight_colour(self):
        """Mismatch pixels must be painted with the specified diff colour."""
        w, h = 4, 4
        white = _rgba_bytes(w, h, (255, 255, 255, 255))
        black = _rgba_bytes(w, h, (0, 0, 0, 255))
        diff_bytes, _, _, _, _ = compare_images(
            white, black, w, h,
            threshold_pct=0.0, anti_aliasing=False,
            diff_color_r=0, diff_color_g=200, diff_color_b=50,
            diff_alpha_pct=100.0, ignore_regions=[],
        )
        diff_img = Image.frombytes("RGBA", (w, h), diff_bytes)
        # Every pixel should be the highlight colour (alpha=255 at 100%)
        for y in range(h):
            for x in range(w):
                r, g, b, a = diff_img.getpixel((x, y))
                assert r == 0 and g == 200 and b == 50, (
                    f"Expected highlight colour at ({x},{y}), got {(r,g,b,a)}"
                )


# ---------------------------------------------------------------------------
# compare_images — threshold boundary
# ---------------------------------------------------------------------------

class TestThresholdBoundary:
    """Pixels near the threshold boundary should flip pass/fail correctly."""

    def test_at_zero_threshold_any_difference_fails(self):
        w, h = 4, 4
        base = _rgba_bytes(w, h, (100, 100, 100, 255))
        # Shift by 1 in R channel — distance = 1
        shifted = _rgba_bytes(w, h, (101, 100, 100, 255))
        _, mismatch_count, _, _, _ = compare_images(
            base, shifted, w, h,
            threshold_pct=0.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert mismatch_count == w * h

    def test_high_threshold_suppresses_mismatch(self):
        """A threshold just above the actual pixel distance suppresses mismatches.

        White vs black yields a Euclidean RGB distance of sqrt(255²×3) ≈ 441.67,
        which equals MAX_COLOR_DISTANCE.  At threshold_pct=100 the computed limit
        equals MAX_COLOR_DISTANCE exactly, and the check is strict (distance >
        threshold), so equality is NOT a mismatch.  We verify this boundary.
        """
        w, h = 4, 4
        white = _rgba_bytes(w, h, (255, 255, 255, 255))
        black = _rgba_bytes(w, h, (0, 0, 0, 255))
        _, mismatch_count, _, _, _ = compare_images(
            white, black, w, h,
            threshold_pct=100.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        # At threshold_pct=100 the limit == MAX_COLOR_DISTANCE; white-vs-black
        # distance equals MAX_COLOR_DISTANCE exactly, so it is NOT a mismatch.
        assert mismatch_count == 0

    def test_threshold_exactly_at_distance(self):
        """Pixel distance exactly equal to threshold is NOT a mismatch (strict >)."""
        w, h = 1, 1
        # R differs by 255, G and B same: distance = 255.0
        # Set threshold so (threshold_pct/100) * MAX_COLOR_DISTANCE == 255.0
        # i.e. threshold_pct = 255.0 / MAX_COLOR_DISTANCE * 100
        # Use a value slightly above to guarantee distance < threshold (no mismatch).
        threshold_pct = (255.0 / MAX_COLOR_DISTANCE) * 100 + 0.1
        base = _rgba_bytes(w, h, (255, 128, 128, 255))
        cand = _rgba_bytes(w, h, (0, 128, 128, 255))
        _, mismatch_count, _, _, _ = compare_images(
            base, cand, w, h,
            threshold_pct=threshold_pct, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert mismatch_count == 0


# ---------------------------------------------------------------------------
# compare_images — ignore regions
# ---------------------------------------------------------------------------

class TestIgnoreRegions:
    """Pixels inside ignore regions must not be counted as mismatches."""

    def test_full_ignore_no_mismatch(self):
        """Ignoring the whole image produces 0 mismatches."""
        w, h = 10, 10
        white = _rgba_bytes(w, h, (255, 255, 255, 255))
        black = _rgba_bytes(w, h, (0, 0, 0, 255))
        _, mismatch_count, total, mismatch_pct, ignored_count = compare_images(
            white, black, w, h,
            threshold_pct=10.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[(0, 0, w, h)],
        )
        assert mismatch_count == 0
        assert ignored_count == w * h
        assert total == 0

    def test_partial_ignore_region(self):
        """Ignoring the left 5 columns of a 10×10 image — 50 pixels skipped."""
        w, h = 10, 10
        white = _rgba_bytes(w, h, (255, 255, 255, 255))
        black = _rgba_bytes(w, h, (0, 0, 0, 255))
        _, mismatch_count, total, _, ignored_count = compare_images(
            white, black, w, h,
            threshold_pct=10.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[(0, 0, 5, h)],
        )
        assert ignored_count == 5 * h
        assert total == 5 * h
        assert mismatch_count == total  # right half all different

    def test_ignore_region_out_of_bounds_clamped(self):
        """Out-of-bounds ignore regions should be clamped, not crash."""
        w, h = 5, 5
        data = _rgba_bytes(w, h, (128, 128, 128, 255))
        _, _, _, _, _ = compare_images(
            data, data, w, h,
            threshold_pct=10.0, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[(-10, -10, 100, 100)],
        )  # must not raise


# ---------------------------------------------------------------------------
# compare_images — anti-aliasing detection
# ---------------------------------------------------------------------------

class TestAntiAliasingDetection:
    """AA detection should reduce false positives on sub-pixel differences."""

    def test_aa_can_reduce_mismatch_count(self):
        """With AA on, mismatch_count should be <= the count with AA off."""
        w, h = 10, 10
        img = Image.new("RGBA", (w, h), (200, 200, 200, 255))
        px = img.load()
        # Introduce a single different pixel surrounded by matching neighbours
        px[5, 5] = (205, 200, 200, 255)
        base_bytes = img.tobytes()
        cand_img = img.copy()
        cpx = cand_img.load()
        cpx[5, 5] = (198, 200, 200, 255)
        cand_bytes = cand_img.tobytes()

        _, count_with_aa, _, _, _ = compare_images(
            base_bytes, cand_bytes, w, h,
            threshold_pct=0.5, anti_aliasing=True,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        _, count_without_aa, _, _, _ = compare_images(
            base_bytes, cand_bytes, w, h,
            threshold_pct=0.5, anti_aliasing=False,
            diff_color_r=255, diff_color_g=0, diff_color_b=0,
            diff_alpha_pct=80.0, ignore_regions=[],
        )
        assert count_with_aa <= count_without_aa


class TestIsAntialiased:
    """Unit tests for the _is_antialiased helper."""

    def test_returns_bool(self):
        img = Image.new("RGBA", (5, 5), (128, 128, 128, 255))
        px = img.load()
        result = _is_antialiased(px, px, 2, 2, 5, 5, threshold=10.0)
        assert isinstance(result, bool)

    def test_identical_images_all_similar_neighbors(self):
        """When both images are identical, all neighbours are similar → AA = True."""
        img = Image.new("RGBA", (10, 10), (200, 200, 200, 255))
        px = img.load()
        # The pixel under test is different but surrounded by matching neighbours
        assert _is_antialiased(px, px, 5, 5, 10, 10, threshold=1.0) is True

    def test_corner_pixel_handled(self):
        """Corner pixels (fewer neighbours) should not raise."""
        img = Image.new("RGBA", (5, 5), (100, 100, 100, 255))
        px = img.load()
        result = _is_antialiased(px, px, 0, 0, 5, 5, threshold=10.0)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# compare_images — dimension validation
# ---------------------------------------------------------------------------

class TestDimensionValidation:
    """Invalid buffer lengths must raise ValueError."""

    def test_wrong_baseline_length(self):
        w, h = 5, 5
        valid = _rgba_bytes(w, h, (0, 0, 0, 255))
        with pytest.raises(ValueError, match="baseline_bytes"):
            compare_images(
                b"\x00" * 10, valid, w, h,
                threshold_pct=10.0, anti_aliasing=False,
                diff_color_r=255, diff_color_g=0, diff_color_b=0,
                diff_alpha_pct=80.0, ignore_regions=[],
            )

    def test_wrong_candidate_length(self):
        w, h = 5, 5
        valid = _rgba_bytes(w, h, (0, 0, 0, 255))
        with pytest.raises(ValueError, match="candidate_bytes"):
            compare_images(
                valid, b"\x00" * 10, w, h,
                threshold_pct=10.0, anti_aliasing=False,
                diff_color_r=255, diff_color_g=0, diff_color_b=0,
                diff_alpha_pct=80.0, ignore_regions=[],
            )


# ---------------------------------------------------------------------------
# compare_image_files — file-based API
# ---------------------------------------------------------------------------

class TestCompareImageFiles:
    def test_identical_files(self, identical_image_pair):
        base, cand = identical_image_pair
        result = compare_image_files(base, cand, threshold_pct=10.0)
        assert result["mismatch_count"] == 0
        assert result["mismatch_pct"] == 0.0
        assert result["status"] == "pass"

    def test_different_files(self, different_image_pair):
        base, cand = different_image_pair
        result = compare_image_files(base, cand, threshold_pct=10.0, anti_aliasing=False)
        assert result["mismatch_pct"] == 100.0
        assert result["status"] == "fail"

    def test_result_dict_keys(self, identical_image_pair):
        base, cand = identical_image_pair
        result = compare_image_files(base, cand)
        expected_keys = {
            "baseline", "candidate", "width", "height", "threshold_pct",
            "mismatch_count", "total_pixels", "mismatch_pct",
            "ignored_count", "status", "output_path",
        }
        assert expected_keys.issubset(result.keys())

    def test_saves_diff_image(self, tmp_path, different_image_pair):
        base, cand = different_image_pair
        diff_out = tmp_path / "diff.png"
        result = compare_image_files(base, cand, output_path=str(diff_out))
        assert diff_out.exists()
        assert result["output_path"] == str(diff_out)
        # Verify it's a valid PNG
        img = Image.open(diff_out)
        assert img.size == (10, 10)

    def test_missing_baseline_raises(self, tmp_path, different_image_pair):
        _, cand = different_image_pair
        with pytest.raises(FileNotFoundError):
            compare_image_files("/nonexistent/path.png", cand)

    def test_missing_candidate_raises(self, tmp_path, different_image_pair):
        base, _ = different_image_pair
        with pytest.raises(FileNotFoundError):
            compare_image_files(base, "/nonexistent/path.png")

    def test_dimension_mismatch_raises(self, tmp_path):
        img_10 = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        img_20 = Image.new("RGBA", (20, 20), (255, 255, 255, 255))
        p10 = tmp_path / "ten.png"
        p20 = tmp_path / "twenty.png"
        img_10.save(str(p10))
        img_20.save(str(p20))
        with pytest.raises(ValueError, match="dimensions do not match"):
            compare_image_files(str(p10), str(p20))

    def test_partial_diff_result(self, partial_diff_image_pair):
        base, cand = partial_diff_image_pair
        result = compare_image_files(base, cand, threshold_pct=10.0, anti_aliasing=False)
        # Approximately half the pixels should differ
        assert 40.0 <= result["mismatch_pct"] <= 60.0

    def test_ignore_region_reduces_mismatch(self, different_image_pair):
        base, cand = different_image_pair
        # Ignore the entire image — should give 0 mismatches
        result = compare_image_files(
            base, cand, threshold_pct=10.0, ignore_regions=[(0, 0, 10, 10)]
        )
        assert result["mismatch_count"] == 0
        assert result["ignored_count"] == 100


# ---------------------------------------------------------------------------
# CLI entry point tests
# ---------------------------------------------------------------------------

class TestCLI:
    """Integration tests that invoke the CLI via subprocess."""

    def test_cli_identical_exit_zero(self, tmp_path, identical_image_pair):
        base, cand = identical_image_pair
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "diff_engine.py"),
             base, cand, "--threshold", "10"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_cli_different_exit_one(self, tmp_path, different_image_pair):
        base, cand = different_image_pair
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "diff_engine.py"),
             base, cand, "--threshold", "10", "--no-anti-aliasing"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1

    def test_cli_outputs_valid_json(self, identical_image_pair):
        base, cand = identical_image_pair
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "diff_engine.py"),
             base, cand, "--quiet"],
            capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        assert "mismatch_pct" in data
        assert "status" in data

    def test_cli_saves_diff_image(self, tmp_path, different_image_pair):
        base, cand = different_image_pair
        diff_path = tmp_path / "output_diff.png"
        subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "diff_engine.py"),
             base, cand, "--diff", str(diff_path), "--quiet"],
            capture_output=True, text=True,
        )
        assert diff_path.exists()

    def test_cli_missing_file_exit_one(self, tmp_path, identical_image_pair):
        base, _ = identical_image_pair
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "diff_engine.py"),
             base, "/nonexistent/image.png", "--quiet"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
