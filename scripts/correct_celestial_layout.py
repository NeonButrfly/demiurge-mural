#!/usr/bin/env python3
"""Correct the celestial layout using the supplied grayscale reference.

The accepted issue #11 anatomy master is authoritative everywhere except the
two celestial circles. This script places the reference eclipse at upper left
and the reference star field at upper right through feathered circular masks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


CELESTIAL_REGIONS = (
    {
        "name": "upper_left_eclipse",
        "source_center": (135, 164),
        "source_radius": 64,
        "destination_center": (292, 373),
        "destination_radius": 122,
        "feather": 8,
    },
    {
        "name": "upper_right_star_field",
        "source_center": (1037, 108),
        "source_radius": 94,
        "destination_center": (1813, 224),
        "destination_radius": 112,
        "feather": 8,
    },
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def circular_mask(diameter: int, radius: float, feather: float) -> np.ndarray:
    yy, xx = np.mgrid[0:diameter, 0:diameter]
    center = (diameter - 1) / 2.0
    distance = np.sqrt((xx - center) ** 2 + (yy - center) ** 2)
    return np.clip((radius - distance) / max(feather, 1.0), 0.0, 1.0).astype(np.float32)


def transplant_circle(
    base: Image.Image,
    reference: Image.Image,
    source_center: tuple[int, int],
    source_radius: int,
    destination_center: tuple[int, int],
    destination_radius: int,
    feather: int,
) -> tuple[Image.Image, Image.Image]:
    source_box = (
        source_center[0] - source_radius,
        source_center[1] - source_radius,
        source_center[0] + source_radius,
        source_center[1] + source_radius,
    )
    diameter = destination_radius * 2
    insert = reference.crop(source_box).resize((diameter, diameter), Image.Resampling.LANCZOS)
    alpha = circular_mask(diameter, destination_radius, feather)

    base_arr = np.asarray(base.convert("L"), dtype=np.float32).copy()
    insert_arr = np.asarray(insert.convert("L"), dtype=np.float32)
    x0 = destination_center[0] - destination_radius
    y0 = destination_center[1] - destination_radius
    target = base_arr[y0 : y0 + diameter, x0 : x0 + diameter]
    base_arr[y0 : y0 + diameter, x0 : x0 + diameter] = target * (1.0 - alpha) + insert_arr * alpha

    full_mask = np.zeros_like(base_arr, dtype=np.uint8)
    full_mask[y0 : y0 + diameter, x0 : x0 + diameter] = np.clip(np.rint(alpha * 255), 0, 255).astype(np.uint8)
    return (
        Image.fromarray(np.clip(np.rint(base_arr), 0, 255).astype(np.uint8), mode="L"),
        Image.fromarray(full_mask, mode="L"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("anatomy_master", type=Path)
    parser.add_argument("celestial_reference", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()

    args.output_directory.mkdir(parents=True, exist_ok=True)
    base = Image.open(args.anatomy_master).convert("L")
    reference = Image.open(args.celestial_reference).convert("L")
    if base.size != (2048, 2048):
        raise ValueError(f"Expected a 2048 x 2048 anatomy master, got {base.size}")
    if reference.size != (1131, 1131):
        raise ValueError(f"Expected an 1131 x 1131 celestial reference, got {reference.size}")

    final = base
    combined_mask = Image.new("L", base.size, 0)
    for region in CELESTIAL_REGIONS:
        final, region_mask = transplant_circle(
            final,
            reference,
            region["source_center"],
            region["source_radius"],
            region["destination_center"],
            region["destination_radius"],
            region["feather"],
        )
        region_mask.save(args.output_directory / f"{region['name']}_mask.png")
        combined_mask = Image.fromarray(
            np.maximum(np.asarray(combined_mask), np.asarray(region_mask)).astype(np.uint8), mode="L"
        )

    combined_mask.save(args.output_directory / "celestial_layout_correction_mask.png")
    final_path = args.output_directory / "demiurge_grayscale_cybernetic_anatomy_corrected_celestials_2048.png"
    final.save(final_path)
    final.crop((112, 193, 472, 553)).save(args.output_directory / "corrected_upper_left_eclipse_crop.png")
    final.crop((1633, 44, 1993, 404)).save(args.output_directory / "corrected_upper_right_star_field_crop.png")

    base_arr = np.asarray(base, dtype=np.int16)
    final_arr = np.asarray(final, dtype=np.int16)
    diff = np.abs(final_arr - base_arr)
    changed = diff > 0
    allowed = np.asarray(combined_mask) > 0
    rgb = np.asarray(final.convert("RGB"), dtype=np.uint8)
    manifest = {
        "issue": 11,
        "acceptance_correction": "upper-left eclipse and upper-right star field per supplied grayscale reference",
        "anatomy_master": str(args.anatomy_master),
        "celestial_reference": str(args.celestial_reference),
        "anatomy_master_sha256": sha256(args.anatomy_master),
        "celestial_reference_sha256": sha256(args.celestial_reference),
        "output": str(final_path),
        "output_sha256": sha256(final_path),
        "dimensions_px": list(final.size),
        "mode": final.mode,
        "neutral_grayscale_rgb_channels_identical": bool(
            np.array_equal(rgb[..., 0], rgb[..., 1]) and np.array_equal(rgb[..., 1], rgb[..., 2])
        ),
        "regions": list(CELESTIAL_REGIONS),
        "changed_pixels": int(changed.sum()),
        "changed_pixels_outside_documented_mask": int(np.logical_and(changed, ~allowed).sum()),
        "mean_absolute_difference_from_anatomy_master": float(diff.mean()),
        "maximum_absolute_difference_from_anatomy_master": int(diff.max()),
        "preservation_policy": {
            "anatomy_pass": "preserved exactly outside the two celestial masks",
            "architecture_bodies_cybernetics": "preserved exactly outside the two celestial masks",
            "upper_left": "reference eclipse transplanted with feathered circular mask",
            "upper_right": "reference star field transplanted with feathered circular mask",
        },
        "unverified": ["relief conversion", "slicer preview", "physical print"],
    }
    (args.output_directory / "celestial_layout_correction_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
