"""Prepare color-review masks and context crops for issue #12."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"
ANNOTATED = Path(r"C:\Users\Keifm\OneDrive\Desktop\Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration.png")
REFERENCE = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\demiurge_full_four_panel_source_2048x2048_grayscale.png")
WORK = ROOT / "work" / "v9_review_corrections"
ASSETS = ROOT / "assets"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def clean(mask: np.ndarray, close: int = 7) -> np.ndarray:
    binary = (mask.astype(np.uint8) * 255)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats((binary > 0).astype(np.uint8), 8)
    result = np.zeros_like(binary)
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) >= 35:
            result[labels == label] = 255
    return result


def crop_with_context(image: np.ndarray, mask: np.ndarray, name: str, pad: int) -> dict[str, int]:
    x, y, width, height = cv2.boundingRect((mask > 0).astype(np.uint8))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(image.shape[1], x + width + pad)
    y1 = min(image.shape[0], y + height + pad)
    save(WORK / f"{name}_target.png", image[y0:y1, x0:x1])
    save(WORK / f"{name}_mask.png", mask[y0:y1, x0:x1])
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    marked = cv2.imread(str(ANNOTATED), cv2.IMREAD_COLOR)
    reference = cv2.imread(str(REFERENCE), cv2.IMREAD_COLOR)
    if base is None or marked is None or reference is None:
        raise FileNotFoundError("Base or annotated review image is missing")
    if base.shape != marked.shape:
        raise AssertionError(f"Shape mismatch: base={base.shape}, annotation={marked.shape}")

    b, g, r = cv2.split(marked)
    yy, xx = np.indices(r.shape)
    masks = {
        "yellow_claw_wing": clean((r > 105) & (g > 90) & (r > b * 1.22) & (g > b * 1.15) & (yy < 175)),
        "red_bulbs": clean((r > 105) & (r > g * 1.28) & (r > b * 1.22)),
        "blue_reclining": clean((b > 85) & (b > g * 1.12) & (b > r * 1.18) & (yy > 820)),
        "green_heads": clean((g > 90) & (g > r * 1.18) & (g > b * 1.12) & (yy > 850)),
        "purple_hooded_arm": clean((b > g * 1.22) & (r > g * 1.18) & (xx > 250) & (xx < 535) & (yy > 590) & (yy < 775)),
    }
    if any(np.count_nonzero(mask) == 0 for mask in masks.values()):
        raise AssertionError("One or more annotation colors could not be isolated")

    # Slightly expand the ownerless-object masks so the full unwanted silhouettes are replaced.
    masks["red_bulbs"] = cv2.dilate(masks["red_bulbs"], np.ones((9, 9), np.uint8), iterations=1)
    masks["green_heads"] = cv2.dilate(masks["green_heads"], np.ones((7, 7), np.uint8), iterations=1)
    # The review requests anatomical integration, which requires the complete limb-to-wing junction,
    # not only the translucent paint footprint across the claw tips.
    cv2.fillPoly(
        masks["yellow_claw_wing"],
        [np.array([[690, 28], [925, 12], [968, 83], [935, 171], [870, 226], [780, 229], [718, 173]], np.int32)],
        255,
    )
    # Include the complete reclining donor silhouette so its head, neck, torso, hips and legs share
    # one tonal treatment instead of leaving a rectangular or disembodied transition.
    cv2.fillPoly(
        masks["blue_reclining"],
        [np.array([[650, 890], [790, 875], [920, 945], [1140, 1115], [1150, 1248], [680, 1248], [645, 1090]], np.int32)],
        255,
    )

    union = np.zeros(base.shape[:2], np.uint8)
    manifest: dict[str, object] = {"issue": 12, "base": str(BASE.relative_to(ROOT)), "regions": {}}
    pads = {
        "yellow_claw_wing": 95,
        "red_bulbs": 40,
        "blue_reclining": 90,
        "green_heads": 65,
        "purple_hooded_arm": 85,
    }
    colors = {
        "yellow_claw_wing": (0, 210, 235),
        "red_bulbs": (30, 30, 235),
        "blue_reclining": (220, 90, 30),
        "green_heads": (45, 215, 70),
        "purple_hooded_arm": (190, 70, 175),
    }
    preview = base.astype(np.float32)
    fixed_generated_bounds = {
        "yellow_claw_wing": {"x0": 621, "y0": 0, "x1": 1027, "y1": 234},
        "blue_reclining": {"x0": 583, "y0": 819, "x1": 1185, "y1": 1254},
    }
    for name, mask in masks.items():
        union = cv2.bitwise_or(union, mask)
        save(ASSETS / f"Pass7_v9_{name}_Mask.png", mask)
        if name in fixed_generated_bounds:
            bounds = fixed_generated_bounds[name]
            save(
                WORK / f"{name}_target.png",
                base[bounds["y0"] : bounds["y1"], bounds["x0"] : bounds["x1"]],
            )
            save(
                WORK / f"{name}_mask.png",
                mask[bounds["y0"] : bounds["y1"], bounds["x0"] : bounds["x1"]],
            )
        else:
            bounds = crop_with_context(base, mask, name, pads[name])
        manifest["regions"][name] = {"pixels": int(np.count_nonzero(mask)), "bounds": bounds}
        alpha = (mask.astype(np.float32) / 255.0 * 0.58)[:, :, None]
        preview = preview * (1.0 - alpha) + np.full_like(preview, colors[name], np.float32) * alpha

    reference = cv2.resize(reference, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_AREA)
    purple_bounds = manifest["regions"]["purple_hooded_arm"]["bounds"]
    save(
        WORK / "purple_hooded_arm_original_reference.png",
        reference[purple_bounds["y0"] : purple_bounds["y1"], purple_bounds["x0"] : purple_bounds["x1"]],
    )

    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (masks["red_bulbs"] > 0).astype(np.uint8), 8
    )
    red_components = 0
    red_tiles: list[np.ndarray] = []
    red_tile_manifest: list[dict[str, int]] = []
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) < 100:
            continue
        component = np.zeros_like(masks["red_bulbs"])
        component[labels == label] = 255
        save(WORK / f"red_component_{red_components:02d}_mask.png", component)
        x, y, width, height = cv2.boundingRect((component > 0).astype(np.uint8))
        side = max(width, height) + 110
        cx, cy = x + width // 2, y + height // 2
        x0 = int(np.clip(cx - side // 2, 0, base.shape[1] - side))
        y0 = int(np.clip(cy - side // 2, 0, base.shape[0] - side))
        x1, y1 = x0 + side, y0 + side
        tile = cv2.resize(marked[y0:y1, x0:x1], (256, 256), interpolation=cv2.INTER_LANCZOS4)
        red_tiles.append(tile)
        red_tile_manifest.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1})
        red_components += 1
    manifest["red_components"] = red_components
    manifest["red_tiles"] = red_tile_manifest
    if red_components != 6:
        raise AssertionError(f"Expected six red review regions, found {red_components}")
    collage = np.zeros((512, 768, 3), np.uint8)
    for index, tile in enumerate(red_tiles):
        row, column = divmod(index, 3)
        collage[row * 256 : (row + 1) * 256, column * 256 : (column + 1) * 256] = tile
    save(WORK / "red_bulbs_repair_collage.png", collage)

    save(ASSETS / "Pass7_v9_Review_Corrections_Union_Mask.png", union)
    save(ROOT / "outputs" / "Pass7_v9_Review_Corrections_Mask_Preview.png", np.clip(preview, 0, 255).astype(np.uint8))
    manifest["union_pixels"] = int(np.count_nonzero(union))
    manifest["outside_mask_policy"] = "all final pixels outside the union remain byte-identical to v7"
    (ASSETS / "Pass7_v9_Review_Corrections_Manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
