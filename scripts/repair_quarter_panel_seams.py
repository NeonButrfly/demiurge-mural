#!/usr/bin/env python3
"""Repair the two center seams in the 2x2 Demiurge mural source.

The repair deliberately leaves all pixels outside narrow center bands untouched.
It measures the apparent panel drift for diagnostics, then bridges each hard join
with a cubic interpolation across only a few pixels. This avoids the broad blur
and ghosting produced by large-area warps on densely detailed artwork.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def estimate_vertical_shift(image: np.ndarray, center: int, search: int = 16) -> tuple[int, list[dict[str, float]]]:
    """Find the y shift that best aligns the right edge with the left edge."""
    height = image.shape[0]
    left = image[:, center - 8 : center].mean(axis=1)
    right = image[:, center : center + 8].mean(axis=1)
    scores: list[dict[str, float]] = []
    for shift in range(-search, search + 1):
        start_left = max(0, -shift)
        stop_left = min(height, height - shift)
        start_right = max(0, shift)
        stop_right = min(height, height + shift)
        score = float(np.abs(left[start_left:stop_left] - right[start_right:stop_right]).mean())
        scores.append({"shift_px": shift, "mean_absolute_error": score})
    best = min(scores, key=lambda entry: entry["mean_absolute_error"])
    return int(best["shift_px"]), scores


def estimate_horizontal_shift(image: np.ndarray, center: int, search: int = 16) -> tuple[int, list[dict[str, float]]]:
    """Find the x shift that best aligns the lower edge with the upper edge."""
    width = image.shape[1]
    upper = image[center - 8 : center].mean(axis=0)
    lower = image[center : center + 8].mean(axis=0)
    scores: list[dict[str, float]] = []
    for shift in range(-search, search + 1):
        start_upper = max(0, -shift)
        stop_upper = min(width, width - shift)
        start_lower = max(0, shift)
        stop_lower = min(width, width + shift)
        score = float(np.abs(upper[start_upper:stop_upper] - lower[start_lower:stop_lower]).mean())
        scores.append({"shift_px": shift, "mean_absolute_error": score})
    best = min(scores, key=lambda entry: entry["mean_absolute_error"])
    return int(best["shift_px"]), scores


def sample_rows(image: np.ndarray, coordinates: np.ndarray) -> np.ndarray:
    height = image.shape[0]
    coordinates = np.clip(coordinates, 0.0, height - 1.0)
    low = np.floor(coordinates).astype(np.int32)
    high = np.minimum(low + 1, height - 1)
    fraction = (coordinates - low)[:, None, None]
    return image[low] * (1.0 - fraction) + image[high] * fraction


def sample_columns(image: np.ndarray, coordinates: np.ndarray) -> np.ndarray:
    width = image.shape[1]
    coordinates = np.clip(coordinates, 0.0, width - 1.0)
    low = np.floor(coordinates).astype(np.int32)
    high = np.minimum(low + 1, width - 1)
    fraction = (coordinates - low)[None, :, None]
    return image[:, low] * (1.0 - fraction) + image[:, high] * fraction


def cubic_bridge_vertical(image: np.ndarray, center: int, radius: int) -> None:
    """Replace only the center columns with a gradient-continuous bridge."""
    x0 = center - radius - 1
    x1 = center + radius
    length = float(x1 - x0)
    value0 = image[:, x0].copy()
    value1 = image[:, x1].copy()
    slope0 = image[:, x0] - image[:, x0 - 1]
    slope1 = image[:, x1 + 1] - image[:, x1]
    for x in range(x0 + 1, x1):
        t = (x - x0) / length
        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2
        image[:, x] = h00 * value0 + h10 * length * slope0 + h01 * value1 + h11 * length * slope1


def cubic_bridge_horizontal(image: np.ndarray, center: int, radius: int) -> None:
    """Replace only the center rows with a gradient-continuous bridge."""
    y0 = center - radius - 1
    y1 = center + radius
    length = float(y1 - y0)
    value0 = image[y0].copy()
    value1 = image[y1].copy()
    slope0 = image[y0] - image[y0 - 1]
    slope1 = image[y1 + 1] - image[y1]
    for y in range(y0 + 1, y1):
        t = (y - y0) / length
        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2
        image[y] = h00 * value0 + h10 * length * slope0 + h01 * value1 + h11 * length * slope1


def seam_statistics(image: np.ndarray, center_x: int, center_y: int) -> dict[str, float]:
    vertical = np.abs(image[:, center_x] - image[:, center_x - 1]).mean(axis=1)
    horizontal = np.abs(image[center_y] - image[center_y - 1]).mean(axis=1)
    return {
        "vertical_mean_absolute_step": float(vertical.mean()),
        "vertical_p95_absolute_step": float(np.percentile(vertical, 95)),
        "vertical_max_absolute_step": float(vertical.max()),
        "horizontal_mean_absolute_step": float(horizontal.mean()),
        "horizontal_p95_absolute_step": float(np.percentile(horizontal, 95)),
        "horizontal_max_absolute_step": float(horizontal.max()),
    }


def save_quadrants(image: Image.Image, directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    width, height = image.size
    center_x, center_y = width // 2, height // 2
    panels = [
        ("panel_01_upper_left.png", (0, 0, center_x, center_y)),
        ("panel_02_upper_right.png", (center_x, 0, width, center_y)),
        ("panel_03_lower_left.png", (0, center_y, center_x, height)),
        ("panel_04_lower_right.png", (center_x, center_y, width, height)),
    ]
    saved: list[str] = []
    for name, box in panels:
        target = directory / name
        image.crop(box).save(target)
        saved.append(str(target))
    return saved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--bridge-radius", type=int, default=4)
    args = parser.parse_args()

    args.output_directory.mkdir(parents=True, exist_ok=True)
    original_image = Image.open(args.source).convert("RGB")
    if original_image.size != (2048, 2048):
        raise ValueError(f"Expected a 2048x2048 source, got {original_image.size}")

    original = np.asarray(original_image, dtype=np.float32)
    repaired = original.copy()
    center_x = repaired.shape[1] // 2
    center_y = repaired.shape[0] // 2

    vertical_shift, vertical_scores = estimate_vertical_shift(original, center_x)
    horizontal_shift, horizontal_scores = estimate_horizontal_shift(original, center_y)

    cubic_bridge_vertical(repaired, center_x, args.bridge_radius)
    cubic_bridge_horizontal(repaired, center_y, args.bridge_radius)
    repaired = np.clip(np.rint(repaired), 0, 255).astype(np.uint8)

    changed = np.any(repaired != original.astype(np.uint8), axis=2)
    allowed = np.zeros_like(changed)
    allowed[:, center_x - args.bridge_radius : center_x + args.bridge_radius] = True
    allowed[center_y - args.bridge_radius : center_y + args.bridge_radius, :] = True
    outside_changes = int(np.count_nonzero(changed & ~allowed))
    if outside_changes:
        raise RuntimeError(f"Repair changed {outside_changes} pixels outside the declared seam bands")

    repaired_image = Image.fromarray(repaired, mode="RGB")
    repaired_path = args.output_directory / "demiurge_full_four_panel_source_2048x2048_seams_repaired.png"
    repaired_image.save(repaired_path)

    original_image.crop((center_x - 128, 0, center_x + 128, original.shape[0])).save(
        args.output_directory / "before_vertical_center_strip.png"
    )
    original_image.crop((0, center_y - 128, original.shape[1], center_y + 128)).save(
        args.output_directory / "before_horizontal_center_strip.png"
    )
    mask = np.zeros((*changed.shape, 3), dtype=np.uint8)
    mask[changed] = (255, 255, 255)
    Image.fromarray(mask, mode="RGB").save(args.output_directory / "seam_repair_changed_pixel_mask.png")
    repaired_image.crop((center_x - 128, 0, center_x + 128, repaired.shape[0])).save(
        args.output_directory / "after_vertical_center_strip.png"
    )
    repaired_image.crop((0, center_y - 128, repaired.shape[1], center_y + 128)).save(
        args.output_directory / "after_horizontal_center_strip.png"
    )

    panels = save_quadrants(repaired_image, args.output_directory / "panels")
    manifest = {
        "source": str(args.source),
        "output": str(repaired_path),
        "dimensions_px": list(repaired_image.size),
        "center_seams_px": {"vertical_x": center_x, "horizontal_y": center_y},
        "estimated_tangent_shifts_px": {
            "right_panel_y": vertical_shift,
            "lower_panel_x": horizontal_shift,
        },
        "repair_bands_px": {"cubic_bridge_radius_per_side": args.bridge_radius},
        "estimated_shifts_are_diagnostic_only": True,
        "changed_pixel_count": int(np.count_nonzero(changed)),
        "changed_pixel_percent": float(np.count_nonzero(changed) * 100.0 / changed.size),
        "changed_pixels_outside_declared_bands": outside_changes,
        "before": seam_statistics(original, center_x, center_y),
        "after": seam_statistics(repaired.astype(np.float32), center_x, center_y),
        "panels": panels,
        "search_scores": {
            "vertical": vertical_scores,
            "horizontal": horizontal_scores,
        },
    }
    (args.output_directory / "seam_repair_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
