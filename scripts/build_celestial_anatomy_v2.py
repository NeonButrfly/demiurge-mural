#!/usr/bin/env python3
"""Restore the mural's eclipse and run a masked local anatomy pass.

The prior grayscale/cybernetic composite remains the authoritative full-frame
artwork. The color reference supplies the distinct upper-right eclipse. A local
SD-Turbo image-to-image pass is restricted to three feathered anatomy masks;
faces, celestial objects, architecture, and all other pixels are preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


PROMPT = (
    "neutral grayscale gothic bas-relief, coherent sculptural anatomy, each arm connected from "
    "shoulder through elbow and wrist to one hand, biomechanical prosthetics attached at natural "
    "joints, no floating hands, no duplicated limbs, preserve composition, crisp cybernetic detail"
)


@dataclass(frozen=True)
class RepairRegion:
    name: str
    box: tuple[int, int, int, int]
    polygons: tuple[tuple[tuple[int, int], ...], ...]
    face_exclusions: tuple[tuple[int, int, int, int], ...]
    strength: float
    blend: float
    seed_offset: int


# Polygon coordinates are local to each 512 x 512 crop. They isolate ambiguous
# limb/joint chains while deliberately avoiding heads and faces.
REGIONS = (
    RepairRegion(
        "central_cybernetic_arm_chain",
        (650, 610, 1162, 1122),
        (
            ((244, 26), (330, 42), (397, 138), (380, 230), (306, 278), (225, 239), (190, 139)),
            ((335, 250), (479, 255), (505, 420), (408, 494), (303, 425), (276, 323)),
        ),
        ((205, 418, 334, 512),),
        0.40,
        0.34,
        0,
    ),
    RepairRegion(
        "middle_limb_ownership",
        (690, 900, 1202, 1412),
        (
            ((72, 26), (180, 30), (268, 132), (254, 253), (168, 330), (66, 269), (20, 142)),
            ((276, 183), (415, 145), (504, 244), (482, 390), (359, 462), (252, 367)),
        ),
        ((103, 91, 222, 222), (296, 268, 425, 396), (328, 399, 455, 512)),
        0.42,
        0.36,
        101,
    ),
    RepairRegion(
        "lower_right_cybernetic_joints",
        (1080, 1030, 1592, 1542),
        (
            ((18, 63), (128, 20), (242, 86), (249, 210), (164, 300), (56, 270)),
            ((211, 228), (349, 173), (488, 244), (509, 401), (397, 494), (244, 443)),
        ),
        ((108, 178, 232, 307), (361, 271, 482, 407), (0, 350, 92, 478)),
        0.40,
        0.34,
        202,
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def luminance(rgb: np.ndarray) -> np.ndarray:
    return np.clip(
        np.rint(rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722),
        0,
        255,
    ).astype(np.uint8)


def histogram_match(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    source_hist = np.bincount(source.ravel(), minlength=256).astype(np.float64)
    reference_hist = np.bincount(reference.ravel(), minlength=256).astype(np.float64)
    source_cdf = np.cumsum(source_hist) / source_hist.sum()
    reference_cdf = np.cumsum(reference_hist) / reference_hist.sum()
    mapping = np.interp(source_cdf, reference_cdf, np.arange(256))
    return np.clip(np.rint(mapping[source]), 0, 255).astype(np.uint8)


def circular_mask(size: tuple[int, int], center: tuple[float, float], radius: float, feather: float) -> np.ndarray:
    width, height = size
    yy, xx = np.mgrid[0:height, 0:width]
    distance = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2)
    return np.clip((radius + feather - distance) / max(feather, 1.0), 0.0, 1.0).astype(np.float32)


def polygon_mask(region: RepairRegion, feather: float = 20.0) -> Image.Image:
    mask = Image.new("L", (512, 512), 0)
    draw = ImageDraw.Draw(mask)
    for polygon in region.polygons:
        draw.polygon(polygon, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))

    # Apply face protection after feathering the repair shape. This guarantees
    # a zero-edit core over each head while retaining a soft transition around it.
    protection = Image.new("L", (512, 512), 255)
    protection_draw = ImageDraw.Draw(protection)
    local_exclusions: list[tuple[int, int, int, int]] = []
    for source_region in REGIONS:
        source_x, source_y = source_region.box[:2]
        for exclusion in source_region.face_exclusions:
            full = (
                source_x + exclusion[0],
                source_y + exclusion[1],
                source_x + exclusion[2],
                source_y + exclusion[3],
            )
            local = (
                full[0] - region.box[0],
                full[1] - region.box[1],
                full[2] - region.box[0],
                full[3] - region.box[1],
            )
            local_exclusions.append(local)
            protection_draw.ellipse(local, fill=0)
    protection = protection.filter(ImageFilter.GaussianBlur(radius=8.0))
    protected = np.asarray(mask, dtype=np.float32) * np.asarray(protection, dtype=np.float32) / 255.0
    protected_image = Image.fromarray(np.clip(np.rint(protected), 0, 255).astype(np.uint8), mode="L")
    protected_draw = ImageDraw.Draw(protected_image)
    for x1, y1, x2, y2 in local_exclusions:
        if x2 - x1 > 16 and y2 - y1 > 16:
            protected_draw.ellipse((x1 + 8, y1 + 8, x2 - 8, y2 - 8), fill=0)
    return protected_image


def restore_eclipse(base: Image.Image, color_reference: Image.Image, grayscale_reference: Image.Image) -> tuple[Image.Image, Image.Image]:
    color_luma = luminance(np.asarray(color_reference.convert("RGB"), dtype=np.uint8))
    gray_luma = luminance(np.asarray(grayscale_reference.convert("RGB"), dtype=np.uint8))
    matched = histogram_match(color_luma, gray_luma)
    tonal = np.clip(np.rint(color_luma * 0.40 + matched * 0.60), 0, 255).astype(np.uint8)

    base_arr = np.asarray(base.convert("L"), dtype=np.float32)
    eclipse_mask = circular_mask(base.size, (1813, 224), 104, 10)
    restored = base_arr * (1.0 - eclipse_mask) + tonal.astype(np.float32) * eclipse_mask
    return (
        Image.fromarray(np.clip(np.rint(restored), 0, 255).astype(np.uint8), mode="L"),
        Image.fromarray(np.clip(np.rint(eclipse_mask * 255), 0, 255).astype(np.uint8), mode="L"),
    )


def load_pipeline(model_id: str):
    import torch
    from diffusers import AutoPipelineForImage2Image

    pipe = AutoPipelineForImage2Image.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe.enable_attention_slicing()
    if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
        pipe.vae.enable_slicing()
    pipe.set_progress_bar_config(desc="Masked local anatomy pass")
    return pipe, torch


def apply_anatomy_repairs(
    base: Image.Image,
    output_directory: Path,
    model_id: str,
    seed: int,
    skip_local_model: bool,
) -> tuple[Image.Image, Image.Image, list[dict[str, object]], float]:
    current = base.convert("L")
    full_mask = Image.new("L", base.size, 0)
    records: list[dict[str, object]] = []
    elapsed = 0.0

    pipe = torch = None
    if not skip_local_model:
        started = time.time()
        pipe, torch = load_pipeline(model_id)
        elapsed += time.time() - started

    for region in REGIONS:
        original_crop = current.crop(region.box).convert("RGB")
        original_crop.save(output_directory / f"{region.name}_before.png")
        local_mask = polygon_mask(region)
        local_mask.save(output_directory / f"{region.name}_mask.png")

        if skip_local_model:
            generated = original_crop.convert("L")
            region_seconds = 0.0
        else:
            assert pipe is not None and torch is not None
            started = time.time()
            generator = torch.Generator(device="cpu").manual_seed(seed + region.seed_offset)
            generated = pipe(
                prompt=PROMPT,
                image=original_crop,
                num_inference_steps=4,
                strength=region.strength,
                guidance_scale=0.0,
                generator=generator,
            ).images[0].convert("L")
            region_seconds = time.time() - started
            elapsed += region_seconds
        generated.save(output_directory / f"{region.name}_model_raw.png")

        original_arr = np.asarray(original_crop.convert("L"), dtype=np.float32)
        generated_arr = np.asarray(generated, dtype=np.float32)
        alpha = np.asarray(local_mask, dtype=np.float32) / 255.0 * region.blend
        repaired_arr = original_arr * (1.0 - alpha) + generated_arr * alpha
        repaired = Image.fromarray(np.clip(np.rint(repaired_arr), 0, 255).astype(np.uint8), mode="L")
        repaired.save(output_directory / f"{region.name}_after.png")

        current.paste(repaired, region.box[:2])
        full_mask_crop = full_mask.crop(region.box)
        full_mask_crop = Image.fromarray(
            np.maximum(np.asarray(full_mask_crop), np.asarray(local_mask)).astype(np.uint8), mode="L"
        )
        full_mask.paste(full_mask_crop, region.box[:2])
        records.append(
            {
                "name": region.name,
                "box": list(region.box),
                "strength": region.strength,
                "blend": region.blend,
                "seed": seed + region.seed_offset,
                "face_exclusions": [list(exclusion) for exclusion in region.face_exclusions],
                "seconds": region_seconds,
            }
        )

    return current, full_mask, records, elapsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prior_composite", type=Path)
    parser.add_argument("grayscale_reference", type=Path)
    parser.add_argument("color_reference", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--model", default="stabilityai/sd-turbo")
    parser.add_argument("--seed", type=int, default=241020)
    parser.add_argument("--skip-local-model", action="store_true")
    args = parser.parse_args()

    args.output_directory.mkdir(parents=True, exist_ok=True)
    prior = Image.open(args.prior_composite).convert("L")
    grayscale_reference = Image.open(args.grayscale_reference).convert("RGB")
    color_reference = Image.open(args.color_reference).convert("RGB")
    if prior.size != (2048, 2048) or color_reference.size != (2048, 2048):
        raise ValueError("The prior composite and color reference must both be 2048 x 2048 pixels")

    celestial_base, eclipse_mask = restore_eclipse(prior, color_reference, grayscale_reference)
    eclipse_mask.save(args.output_directory / "eclipse_restoration_mask.png")
    celestial_base.save(args.output_directory / "celestial_restored_before_anatomy.png")

    final, anatomy_mask, region_records, elapsed = apply_anatomy_repairs(
        celestial_base,
        args.output_directory,
        args.model,
        args.seed,
        args.skip_local_model,
    )
    anatomy_mask.save(args.output_directory / "anatomy_repair_mask.png")
    final_path = args.output_directory / "demiurge_grayscale_cybernetic_celestial_anatomy_master_2048.png"
    final.save(final_path)

    final.crop((112, 193, 472, 553)).save(args.output_directory / "celestial_star_field_crop.png")
    final.crop((1633, 44, 1993, 404)).save(args.output_directory / "celestial_eclipse_crop.png")
    final.crop((512, 512, 1536, 1536)).save(args.output_directory / "anatomy_center_crop.png")

    prior_arr = np.asarray(prior, dtype=np.int16)
    final_arr = np.asarray(final, dtype=np.int16)
    diff = np.abs(final_arr - prior_arr)
    allowed = np.maximum(np.asarray(eclipse_mask), np.asarray(anatomy_mask)) > 0
    changed = diff > 0
    rgb = np.asarray(final.convert("RGB"), dtype=np.uint8)
    manifest = {
        "issue": 11,
        "prior_composite": str(args.prior_composite),
        "grayscale_reference": str(args.grayscale_reference),
        "color_reference": str(args.color_reference),
        "prior_composite_sha256": sha256(args.prior_composite),
        "grayscale_reference_sha256": sha256(args.grayscale_reference),
        "color_reference_sha256": sha256(args.color_reference),
        "output": str(final_path),
        "output_sha256": sha256(final_path),
        "dimensions_px": list(final.size),
        "mode": final.mode,
        "neutral_grayscale_rgb_channels_identical": bool(
            np.array_equal(rgb[..., 0], rgb[..., 1]) and np.array_equal(rgb[..., 1], rgb[..., 2])
        ),
        "grayscale_range": [int(rgb[..., 0].min()), int(rgb[..., 0].max())],
        "changed_pixels": int(changed.sum()),
        "changed_pixels_outside_documented_masks": int(np.logical_and(changed, ~allowed).sum()),
        "mean_absolute_difference_from_prior": float(diff.mean()),
        "maximum_absolute_difference_from_prior": int(diff.max()),
        "local_model": None if args.skip_local_model else args.model,
        "local_model_device": None if args.skip_local_model else "cpu",
        "local_model_prompt": PROMPT,
        "local_model_total_seconds_including_load": elapsed,
        "anatomy_regions": region_records,
        "composition_policy": {
            "full_frame": "prior #10 composite preserved outside documented masks",
            "star_field": "upper-left field preserved from prior composite",
            "eclipse": "upper-right eclipse restored from tone-matched color-reference luminance",
            "anatomy": "three local SD-Turbo crops blended only through feathered polygon masks",
            "faces_architecture_wings_halos": "excluded from anatomy masks",
        },
        "unverified": ["relief conversion", "slicer preview", "physical print"],
    }
    (args.output_directory / "celestial_anatomy_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
