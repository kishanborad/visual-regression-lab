"""
conftest.py — pytest fixtures shared across the visual regression test suite.

Provides synthetic test images built purely from PIL so that the test suite
runs without any external image assets.
"""

from __future__ import annotations

import io
from typing import Generator

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Image factory helpers
# ---------------------------------------------------------------------------

def _solid_rgba_image(
    width: int,
    height: int,
    color: tuple[int, int, int, int] = (128, 128, 128, 255),
) -> Image.Image:
    """Return a solid-colour RGBA image."""
    img = Image.new("RGBA", (width, height), color)
    return img


def _gradient_rgba_image(width: int, height: int) -> Image.Image:
    """Return an RGBA image with a simple horizontal gradient for realism."""
    img = Image.new("RGBA", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            v = int(255 * x / max(width - 1, 1))
            px[x, y] = (v, 128, 255 - v, 255)
    return img


def _checkerboard_image(width: int, height: int, cell: int = 2) -> Image.Image:
    """Return a black-and-white checkerboard RGBA image."""
    img = Image.new("RGBA", (width, height))
    px = img.load()
    for y in range(height):
        for x in range(width):
            is_white = ((x // cell) + (y // cell)) % 2 == 0
            v = 255 if is_white else 0
            px[x, y] = (v, v, v, 255)
    return img


def _to_bytes(img: Image.Image) -> bytes:
    """Return raw RGBA bytes from a PIL image."""
    return img.convert("RGBA").tobytes()


def _save_png(img: Image.Image, path) -> None:
    """Save a PIL image to a file path."""
    img.save(str(path), format="PNG")


# ---------------------------------------------------------------------------
# Session-scoped fixtures (shared across all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def solid_white_image() -> Image.Image:
    """10×10 solid white RGBA image."""
    return _solid_rgba_image(10, 10, (255, 255, 255, 255))


@pytest.fixture(scope="session")
def solid_black_image() -> Image.Image:
    """10×10 solid black RGBA image."""
    return _solid_rgba_image(10, 10, (0, 0, 0, 255))


@pytest.fixture(scope="session")
def solid_red_image() -> Image.Image:
    """10×10 solid red RGBA image."""
    return _solid_rgba_image(10, 10, (255, 0, 0, 255))


@pytest.fixture(scope="session")
def gradient_image() -> Image.Image:
    """20×20 horizontal gradient RGBA image."""
    return _gradient_rgba_image(20, 20)


@pytest.fixture(scope="session")
def checkerboard_image() -> Image.Image:
    """20×20 checkerboard RGBA image."""
    return _checkerboard_image(20, 20)


@pytest.fixture(scope="session")
def image_bytes_white(solid_white_image) -> bytes:
    return _to_bytes(solid_white_image)


@pytest.fixture(scope="session")
def image_bytes_black(solid_black_image) -> bytes:
    return _to_bytes(solid_black_image)


@pytest.fixture(scope="session")
def image_bytes_red(solid_red_image) -> bytes:
    return _to_bytes(solid_red_image)


# ---------------------------------------------------------------------------
# Function-scoped fixtures (fresh per test)
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_baseline_dir(tmp_path) -> Generator:
    """Temporary directory containing baseline PNG images."""
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    yield baseline


@pytest.fixture()
def tmp_candidate_dir(tmp_path) -> Generator:
    """Temporary directory containing candidate PNG images."""
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    yield candidate


@pytest.fixture()
def tmp_output_dir(tmp_path) -> Generator:
    """Temporary directory for batch compare output."""
    output = tmp_path / "reports"
    output.mkdir()
    yield output


@pytest.fixture()
def identical_image_pair(tmp_path) -> tuple[str, str]:
    """A pair of identical 10×10 white PNG files on disk."""
    img = _solid_rgba_image(10, 10, (200, 200, 200, 255))
    base = tmp_path / "identical_baseline.png"
    cand = tmp_path / "identical_candidate.png"
    _save_png(img, base)
    _save_png(img, cand)
    return str(base), str(cand)


@pytest.fixture()
def different_image_pair(tmp_path) -> tuple[str, str]:
    """A baseline (white) vs candidate (black) pair — 100% mismatch."""
    white = _solid_rgba_image(10, 10, (255, 255, 255, 255))
    black = _solid_rgba_image(10, 10, (0, 0, 0, 255))
    base = tmp_path / "diff_baseline.png"
    cand = tmp_path / "diff_candidate.png"
    _save_png(white, base)
    _save_png(black, cand)
    return str(base), str(cand)


@pytest.fixture()
def partial_diff_image_pair(tmp_path) -> tuple[str, str]:
    """Baseline and candidate that differ in only the left half (approx 50%)."""
    base_img = _solid_rgba_image(10, 10, (255, 255, 255, 255))
    cand_img = base_img.copy()
    px = cand_img.load()
    for y in range(10):
        for x in range(5):  # left half changed
            px[x, y] = (0, 0, 0, 255)
    base = tmp_path / "partial_baseline.png"
    cand = tmp_path / "partial_candidate.png"
    _save_png(base_img, base)
    _save_png(cand_img, cand)
    return str(base), str(cand)
