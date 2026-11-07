"""Composite issue #12 corrections with strict out-of-mask byte identity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
GENERATED = ASSETS / "generated"
OUTPUTS = ROOT / "outputs"
WORK = ROOT / "work" / "v9_review_corrections"
BASE = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"
FINAL = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections.png"


def save(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gray3(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    return cv2.boundingRect((mask > 0).astype(np.uint8))


def tone_match(patch: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
    selected = mask > 0
    ring = cv2.dilate(selected.astype(np.uint8), np.ones((21, 21), np.uint8), iterations=1) > 0
    ring &= ~selected
    patch_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY).astype(np.float32)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    source_values = patch_gray[selected]
    target_values = target_gray[ring] if np.count_nonzero(ring) > 32 else target_gray[selected]
    gain = float(np.clip(np.std(target_values) / max(np.std(source_values), 1.0), 0.72, 1.18))
    matched = (patch_gray - float(np.mean(source_values))) * gain + float(np.mean(target_values))
    matched = np.clip(matched, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(matched, (0, 0), 0.75)
    matched = cv2.addWeighted(matched, 1.55, blur, -0.55, 0)
    return cv2.cvtColor(matched, cv2.COLOR_GRAY2BGR)


def place_generated_crop(
    canvas: np.ndarray,
    donor: np.ndarray,
    mask: np.ndarray,
    bounds: dict[str, int],
    feather: float,
    lift: float = 0.0,
) -> None:
    x0, y0, x1, y1 = (bounds[key] for key in ("x0", "y0", "x1", "y1"))
    target = canvas[y0:y1, x0:x1]
    local_mask = mask[y0:y1, x0:x1]
    patch = cv2.resize(donor, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    patch = tone_match(gray3(patch), target, local_mask)
    if lift:
        patch = cv2.convertScaleAbs(patch, alpha=1.0, beta=lift)
    distance = cv2.distanceTransform((local_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / feather, 1.0)[:, :, None]
    mixed = np.clip(target.astype(np.float32) * (1.0 - alpha) + patch.astype(np.float32) * alpha, 0, 255)
    selected = local_mask > 0
    target[selected] = gray3(mixed.astype(np.uint8))[selected]


def replace_red_components(
    canvas: np.ndarray,
    donor_sheet: np.ndarray,
    mask: np.ndarray,
    red_tiles: list[dict[str, int]],
) -> None:
    """Map the user's six externally repaired donor panels into the approved red masks."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    components = []
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) < 100:
            continue
        components.append(label)
    components.sort(key=lambda label: (int(stats[label, cv2.CC_STAT_TOP]), int(stats[label, cv2.CC_STAT_LEFT])))
    if len(components) != 6 or len(red_tiles) != 6:
        raise AssertionError("Expected six external red donor mappings")

    # The external service returned the requested 3x2 grid on a 2848x1600 canvas.
    columns = ((0, 950), (970, 1900), (1925, donor_sheet.shape[1]))
    rows = ((0, 800), (800, donor_sheet.shape[0]))
    donor_panels = []
    for row in rows:
        for column in columns:
            donor_panels.append(donor_sheet[row[0] : row[1], column[0] : column[1]])

    for label, tile_bounds, panel in zip(components, red_tiles, donor_panels, strict=True):
        component = labels == label
        x, y, width, height = cv2.boundingRect(component.astype(np.uint8))
        target = canvas[y : y + height, x : x + width]
        tile_width = tile_bounds["x1"] - tile_bounds["x0"]
        tile_height = tile_bounds["y1"] - tile_bounds["y0"]
        panel = cv2.resize(panel, (tile_width, tile_height), interpolation=cv2.INTER_AREA)
        px0 = x - tile_bounds["x0"]
        py0 = y - tile_bounds["y0"]
        donor = panel[py0 : py0 + height, px0 : px0 + width]
        local_mask = component[y : y + height, x : x + width].astype(np.uint8) * 255
        donor = tone_match(gray3(donor), target, local_mask)
        distance = cv2.distanceTransform((local_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
        alpha = np.minimum(distance / 8.0, 1.0)[:, :, None]
        mixed = np.clip(target.astype(np.float32) * (1.0 - alpha) + donor.astype(np.float32) * alpha, 0, 255)
        selected = local_mask > 0
        target[selected] = gray3(mixed.astype(np.uint8))[selected]


def details(image: np.ndarray) -> np.ndarray:
    crops = [
        image[0:245, 610:1035],
        image[390:625, 205:480],
        image[500:800, 160:575],
        image[805:1254, 570:1195],
    ]
    thumbs = [cv2.resize(crop, (480, 320), interpolation=cv2.INTER_LANCZOS4) for crop in crops]
    return np.vstack((np.hstack(thumbs[:2]), np.hstack(thumbs[2:])))


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    manifest = json.loads((ASSETS / "Pass7_v9_Review_Corrections_Manifest.json").read_text(encoding="utf-8"))
    masks = {
        name: cv2.imread(str(ASSETS / f"Pass7_v9_{name}_Mask.png"), cv2.IMREAD_GRAYSCALE)
        for name in (
            "yellow_claw_wing",
            "red_bulbs",
            "blue_reclining",
            "green_heads",
            "purple_hooded_arm",
        )
    }
    union = cv2.imread(str(ASSETS / "Pass7_v9_Review_Corrections_Union_Mask.png"), cv2.IMREAD_GRAYSCALE)
    yellow = cv2.imread(str(GENERATED / "Pass7_v9_Yellow_Claw_Wing_Donor.png"), cv2.IMREAD_COLOR)
    lower = cv2.imread(str(GENERATED / "Pass7_v9_Blue_Green_Reclining_Donor.png"), cv2.IMREAD_COLOR)
    red_donor = cv2.imread(
        str(GENERATED / "Pass7_v9_External_Red_Bulb_Repairs.png"),
        cv2.IMREAD_COLOR,
    )
    if base is None or union is None or yellow is None or lower is None or red_donor is None or any(value is None for value in masks.values()):
        raise FileNotFoundError("A v9 base, mask, or donor is missing")

    result = base.copy()
    place_generated_crop(
        result,
        yellow,
        masks["yellow_claw_wing"],
        manifest["regions"]["yellow_claw_wing"]["bounds"],
        feather=8.0,
        lift=5.0,
    )
    lower_mask = cv2.bitwise_or(masks["blue_reclining"], masks["green_heads"])
    place_generated_crop(
        result,
        lower,
        lower_mask,
        manifest["regions"]["blue_reclining"]["bounds"],
        feather=11.0,
        lift=14.0,
    )
    replace_red_components(result, red_donor, masks["red_bulbs"], manifest["red_tiles"])
    # The rejected v8 surface treatment is removed by returning to the clean v7 arm.
    # Its already-valid shoulder-to-five-finger chain is intentionally left byte-identical.
    save(FINAL, result)

    selected = union > 0
    absolute = cv2.absdiff(base, result)
    changed = np.any(absolute != 0, axis=2)
    violations = changed & ~selected
    difference_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections_Difference.png"
    out_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections_OutOfMask.png"
    details_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections_Details.png"
    save(difference_path, cv2.convertScaleAbs(absolute, alpha=4.0))
    violation_view = np.zeros_like(result)
    violation_view[violations] = (0, 0, 255)
    save(out_path, violation_view)
    save(details_path, details(result))

    report = {
        "issue": 12,
        "base": str(BASE.relative_to(ROOT)),
        "base_sha256": sha256(BASE),
        "final": str(FINAL.relative_to(ROOT)),
        "final_sha256": sha256(FINAL),
        "dimensions": [int(result.shape[1]), int(result.shape[0])],
        "selected_pixels": int(np.count_nonzero(selected)),
        "changed_pixels": int(np.count_nonzero(changed)),
        "changed_pixels_outside_masks": int(np.count_nonzero(violations)),
        "outside_masks_byte_identical": bool(np.count_nonzero(violations) == 0),
        "changed_pixels_neutral_grayscale": bool(
            np.array_equal(result[:, :, 0][changed], result[:, :, 1][changed])
            and np.array_equal(result[:, :, 1][changed], result[:, :, 2][changed])
        ),
        "repairs": {
            "yellow": "connected five-talon claw and coherent bat wing donor",
            "red": "six ownerless bulbs replaced with adjacent relief texture",
            "blue": "bright tonally matched fully draped reclining figure donor",
            "green": "unattached heads removed within the lower donor footprint",
            "purple": "rejected v8 engraving removed; clean v7 five-finger cybernetic arm restored",
        },
        "generation": "focused built-in edits for yellow and blue/green; user-supplied external six-panel donor for red; deterministic v7 restoration for purple",
    }
    qa_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL,
            difference_path,
            out_path,
            details_path,
            qa_path,
            OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections_Analysis.md",
            OUTPUTS / "Pass7_v9_Review_Corrections_Mask_Preview.png",
            ASSETS / "Pass7_v9_Review_Corrections_Manifest.json",
            ASSETS / "Pass7_v9_Review_Corrections_Union_Mask.png",
            *(ASSETS / f"Pass7_v9_{name}_Mask.png" for name in masks),
            GENERATED / "Pass7_v9_Yellow_Claw_Wing_Donor.png",
            GENERATED / "Pass7_v9_Blue_Green_Reclining_Donor.png",
            GENERATED / "Pass7_v9_External_Red_Bulb_Repairs.png",
        ):
            bundle.write(path, path.relative_to(ROOT))

    if np.count_nonzero(violations):
        raise AssertionError("Pixels changed outside the approved issue #12 mask union")
    if not report["changed_pixels_neutral_grayscale"]:
        raise AssertionError("Changed pixels are not neutral grayscale")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
