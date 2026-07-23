export const DEFAULT_DIFF_SCRIPT = `
from PIL import Image
import struct

def compare_images(
    baseline_bytes, candidate_bytes,
    width, height,
    threshold_pct, anti_aliasing,
    diff_color_r, diff_color_g, diff_color_b, diff_alpha_pct,
    ignore_regions
):
    """
    Compare two RGBA pixel buffers and return a diff buffer + stats.

    Parameters:
        baseline_bytes: bytes - raw RGBA pixel data for baseline
        candidate_bytes: bytes - raw RGBA pixel data for candidate
        width: int - image width
        height: int - image height
        threshold_pct: float - color distance threshold (0-100%)
        anti_aliasing: bool - skip anti-aliased pixels
        diff_color_r/g/b: int - highlight color for mismatched pixels (0-255)
        diff_alpha_pct: float - highlight opacity (0-100%)
        ignore_regions: list of (x, y, w, h) tuples
    """
    baseline = Image.frombytes('RGBA', (width, height), baseline_bytes)
    candidate = Image.frombytes('RGBA', (width, height), candidate_bytes)

    base_px = baseline.load()
    cand_px = candidate.load()

    diff_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    diff_px = diff_img.load()

    max_distance = 441.67  # sqrt(255^2 * 3)
    threshold = (threshold_pct / 100.0) * max_distance
    diff_alpha = int((diff_alpha_pct / 100.0) * 255)

    # Build ignore mask
    ignore_mask = set()
    for (rx, ry, rw, rh) in ignore_regions:
        for iy in range(max(0, ry), min(height, ry + rh)):
            for ix in range(max(0, rx), min(width, rx + rw)):
                ignore_mask.add((ix, iy))

    mismatch_count = 0
    ignored_count = len(ignore_mask)

    for y in range(height):
        for x in range(width):
            if (x, y) in ignore_mask:
                # Copy baseline pixel at reduced opacity for context
                br, bg, bb, ba = base_px[x, y]
                diff_px[x, y] = (br, bg, bb, ba // 4)
                continue

            br, bg, bb, ba = base_px[x, y]
            cr, cg, cb, ca = cand_px[x, y]

            dr = br - cr
            dg = bg - cg
            db = bb - cb
            distance = (dr*dr + dg*dg + db*db) ** 0.5

            if distance > threshold:
                # Anti-aliasing check: if enabled, check if this pixel
                # is surrounded by similar neighbors (likely AA artifact)
                if anti_aliasing and _is_antialiased(base_px, cand_px, x, y, width, height, threshold):
                    # Copy baseline pixel dimmed
                    diff_px[x, y] = (br, bg, bb, ba // 4)
                    continue

                mismatch_count += 1
                diff_px[x, y] = (diff_color_r, diff_color_g, diff_color_b, diff_alpha)
            else:
                # Match — copy baseline pixel dimmed for context
                diff_px[x, y] = (br, bg, bb, ba // 4)

    total_pixels = width * height - ignored_count
    mismatch_pct = (mismatch_count / total_pixels * 100) if total_pixels > 0 else 0

    result_bytes = diff_img.tobytes()
    return (result_bytes, mismatch_count, total_pixels, mismatch_pct, ignored_count)


def _is_antialiased(base_px, cand_px, x, y, w, h, threshold):
    """Check if a differing pixel is likely an anti-aliasing artifact."""
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
                d = (dr*dr + dg*dg + db*db) ** 0.5
                if d <= threshold:
                    similar_neighbors += 1
    # If most neighbors are similar, this pixel is likely anti-aliased
    return total_neighbors > 0 and (similar_neighbors / total_neighbors) >= 0.5
`;
