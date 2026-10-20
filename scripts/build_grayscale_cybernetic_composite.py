#!/usr/bin/env python3
"""Build a neutral-grayscale cybernetic mural composite from two references.

The 2048 px color mural is authoritative for bodies, cybernetics, architecture,
and fine detail. The grayscale anatomy-cleanup reference supplies the tonal
distribution and the star field inserted inside the existing eclipse. A local
SD-Turbo img2img pass harmonizes only the low-frequency appearance; original
high-frequency relief detail and both celestial circles are restored afterward.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


PROMPT = (
    "neutral grayscale gothic bas-relief mural, dense coherent cybernetic figures, "
    "integrated biomechanical limbs and cables, layered bodies, skull mechanisms, "
    "cathedral architecture, polished silver and black carved metal, dramatic relief "
    "lighting, anatomically coherent, continuous composition, extremely detailed"
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


def paste_star_field(base: Image.Image, reference: Image.Image) -> tuple[Image.Image, Image.Image]:
    # Measured from the supplied images at native resolution.
    source_center = (1038, 108)
    source_radius = 78
    destination_center = (1813, 224)
    destination_radius = 76

    ref = np.asarray(reference.convert("L"), dtype=np.uint8)
    source_box = (
        source_center[0] - source_radius,
        source_center[1] - source_radius,
        source_center[0] + source_radius,
        source_center[1] + source_radius,
    )
    star = Image.fromarray(ref, mode="L").crop(source_box).resize(
        (destination_radius * 2, destination_radius * 2), Image.Resampling.LANCZOS
    )
    star_arr = np.asarray(star, dtype=np.float32)

    output = np.asarray(base.convert("L"), dtype=np.float32).copy()
    x0 = destination_center[0] - destination_radius
    y0 = destination_center[1] - destination_radius
    local_mask = circular_mask(
        (destination_radius * 2, destination_radius * 2),
        (destination_radius - 0.5, destination_radius - 0.5),
        destination_radius - 7,
        7,
    )
    target = output[y0 : y0 + destination_radius * 2, x0 : x0 + destination_radius * 2]
    output[y0 : y0 + destination_radius * 2, x0 : x0 + destination_radius * 2] = (
        target * (1.0 - local_mask) + star_arr * local_mask
    )

    full_mask = np.zeros_like(output, dtype=np.float32)
    full_mask[y0 : y0 + destination_radius * 2, x0 : x0 + destination_radius * 2] = local_mask
    return Image.fromarray(np.clip(np.rint(output), 0, 255).astype(np.uint8), mode="L"), Image.fromarray(
        np.clip(np.rint(full_mask * 255), 0, 255).astype(np.uint8), mode="L"
    )


def local_harmonize(base: Image.Image, model_id: str, seed: int) -> tuple[Image.Image, float]:
    import torch
    from diffusers import AutoPipelineForImage2Image

    started = time.time()
    pipe = AutoPipelineForImage2Image.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe.enable_attention_slicing()
    if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
        pipe.vae.enable_slicing()
    pipe.set_progress_bar_config(desc="Local SD-Turbo harmonization")

    initial = base.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    generated = pipe(
        prompt=PROMPT,
        image=initial,
        num_inference_steps=4,
        strength=0.28,
        guidance_scale=0.0,
        generator=generator,
    ).images[0].convert("L")
    del pipe
    return generated, time.time() - started


def restore_high_frequency(base: Image.Image, harmonized: Image.Image) -> Image.Image:
    base_arr = np.asarray(base.convert("L"), dtype=np.float32)
    base_blur = np.asarray(base.filter(ImageFilter.GaussianBlur(radius=2.2)), dtype=np.float32)
    low = harmonized.resize(base.size, Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=0.8))
    low_arr = np.asarray(low, dtype=np.float32)
    # The local model is intentionally subordinate: use only a small fraction of
    # its low-frequency lighting shift while retaining the base image itself.
    combined = np.clip(base_arr + (low_arr - base_blur) * 0.055, 0, 255)

    # Restore both celestial structures exactly from the deterministic composite.
    left_mask = circular_mask(base.size, (292, 373), 132, 16)
    right_mask = circular_mask(base.size, (1813, 224), 112, 14)
    preserve = np.maximum(left_mask, right_mask)[..., None]
    combined_rgb = np.repeat(combined[..., None], 3, axis=2)
    base_rgb = np.repeat(base_arr[..., None], 3, axis=2)
    final = combined_rgb * (1.0 - preserve) + base_rgb * preserve
    gray = np.clip(np.rint(final[..., 0]), 0, 255).astype(np.uint8)
    return Image.fromarray(gray, mode="L")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("grayscale_reference", type=Path)
    parser.add_argument("color_reference", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--model", default="stabilityai/sd-turbo")
    parser.add_argument("--seed", type=int, default=241019)
    parser.add_argument("--skip-local-model", action="store_true")
    args = parser.parse_args()

    args.output_directory.mkdir(parents=True, exist_ok=True)
    grayscale_reference = Image.open(args.grayscale_reference).convert("RGB")
    color_reference = Image.open(args.color_reference).convert("RGB")
    if color_reference.size != (2048, 2048):
        raise ValueError(f"Expected 2048x2048 color reference, got {color_reference.size}")

    color_luma = luminance(np.asarray(color_reference, dtype=np.uint8))
    gray_luma = luminance(np.asarray(grayscale_reference, dtype=np.uint8))
    matched = histogram_match(color_luma, gray_luma)
    # Retain the color mural's local relief contrast while adopting the reference tone curve.
    tonal = np.clip(np.rint(color_luma * 0.40 + matched * 0.60), 0, 255).astype(np.uint8)
    deterministic = Image.fromarray(tonal, mode="L")
    deterministic, star_mask = paste_star_field(deterministic, grayscale_reference)

    deterministic_path = args.output_directory / "demiurge_grayscale_cybernetic_composite_base.png"
    deterministic.save(deterministic_path)
    star_mask.save(args.output_directory / "star_field_insert_mask.png")

    elapsed = 0.0
    if args.skip_local_model:
        harmonized = deterministic.resize((512, 512), Image.Resampling.LANCZOS)
    else:
        harmonized, elapsed = local_harmonize(deterministic, args.model, args.seed)
    harmonized.save(args.output_directory / "local_sd_turbo_harmonization_512.png")

    final = restore_high_frequency(deterministic, harmonized)
    final_path = args.output_directory / "demiurge_grayscale_cybernetic_celestial_master_2048.png"
    final.save(final_path)
    final.crop((112, 193, 472, 553)).save(args.output_directory / "celestial_left_orb_crop.png")
    final.crop((1633, 44, 1993, 404)).save(args.output_directory / "celestial_star_eclipse_crop.png")
    final.crop((512, 512, 1536, 1536)).save(args.output_directory / "cybernetic_body_detail_center.png")

    final_rgb = np.asarray(final.convert("RGB"), dtype=np.uint8)
    manifest = {
        "issue": 10,
        "grayscale_reference": str(args.grayscale_reference),
        "color_reference": str(args.color_reference),
        "grayscale_reference_sha256": sha256(args.grayscale_reference),
        "color_reference_sha256": sha256(args.color_reference),
        "output": str(final_path),
        "output_sha256": sha256(final_path),
        "dimensions_px": list(final.size),
        "mode": final.mode,
        "neutral_grayscale_rgb_channels_identical": bool(
            np.array_equal(final_rgb[..., 0], final_rgb[..., 1])
            and np.array_equal(final_rgb[..., 1], final_rgb[..., 2])
        ),
        "grayscale_range": [int(final_rgb[..., 0].min()), int(final_rgb[..., 0].max())],
        "grayscale_standard_deviation": float(final_rgb[..., 0].std()),
        "local_model": None if args.skip_local_model else args.model,
        "local_model_device": None if args.skip_local_model else "cpu",
        "local_model_seed": args.seed,
        "local_model_seconds_including_load": elapsed,
        "local_prompt": PROMPT,
        "composition_policy": {
            "bodies_cybernetics_architecture": "color reference authoritative",
            "tonal_distribution": "grayscale reference histogram blended 60 percent",
            "star_field": "grayscale reference inserted inside color-reference eclipse",
            "eclipse_ring_and_surround": "color reference preserved",
            "high_frequency_detail": "deterministic 2048px base restored after local diffusion",
            "local_harmonization_influence": "5.5 percent low-frequency delta",
        },
        "unverified": ["relief conversion", "slicer preview", "physical print"],
    }
    (args.output_directory / "composite_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
