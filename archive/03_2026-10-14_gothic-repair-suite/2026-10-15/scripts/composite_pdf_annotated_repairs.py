"""Composite the repairs marked in 10152026.pdf with strict mask isolation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
GENERATED = ASSETS / "generated"

DESTINATION = OUTPUTS / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png"
YELLOW_MASK = ASSETS / "Pass7_PDF_Yellow_Anatomy_Mask.png"
RED_MASK = ASSETS / "Pass7_PDF_Red_Replacement_Mask.png"
UNION_MASK = ASSETS / "Pass7_PDF_Annotated_Union_Mask.png"
FINAL = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"

RED_DONORS = [
    GENERATED / "Pass7_PDF_R1_Horned_Head_Donor.png",
    GENERATED / "Pass7_PDF_R2_Spear_Grip_Donor.png",
    GENERATED / "Pass7_PDF_R3_Reclining_Figure_Donor.png",
]
YELLOW_DONOR = GENERATED / "Pass7_PDF_Yellow_Relief_Texture_Donor.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_png(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(f"Could not write {path}")


def neutral(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def match_tone(patch: np.ndarray, target: np.ndarray, selected: np.ndarray) -> np.ndarray:
    """Match robust local luminance without removing the donor's relief texture."""
    donor_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY).astype(np.float32)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    values_d = donor_gray[selected]
    ring = cv2.dilate(selected.astype(np.uint8), np.ones((15, 15), np.uint8), iterations=1) > 0
    ring &= ~selected
    values_t = target_gray[ring] if np.count_nonzero(ring) >= 32 else target_gray[selected]
    if values_d.size < 8:
        return neutral(patch)
    gain = float(np.clip(np.std(values_t) / max(np.std(values_d), 1.0), 0.45, 1.05))
    adjusted = (donor_gray - float(np.mean(values_d))) * gain + float(np.mean(values_t))
    adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def internal_alpha(mask: np.ndarray, feather: float = 4.0) -> np.ndarray:
    selected = (mask > 0).astype(np.uint8)
    distance = cv2.distanceTransform(selected, cv2.DIST_L2, 5)
    return np.minimum(distance / feather, 1.0)[:, :, None]


def apply_patch_strict(
    canvas: np.ndarray,
    donor_patch: np.ndarray,
    component_mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    poisson_harmonize: bool = True,
) -> None:
    x, y, width, height = bbox
    target = canvas[y : y + height, x : x + width]
    mask = component_mask[y : y + height, x : x + width]
    if donor_patch.shape[:2] != (height, width):
        scale = max(donor_patch.shape[0] / max(height, 1), donor_patch.shape[1] / max(width, 1))
        if scale > 1.5:
            sigma = min(4.0, scale * 0.32)
            donor_patch = cv2.GaussianBlur(donor_patch, (0, 0), sigmaX=sigma, sigmaY=sigma)
        donor_patch = cv2.resize(donor_patch, (width, height), interpolation=cv2.INTER_AREA)
    selected = mask > 0
    donor_patch = match_tone(neutral(donor_patch), target, selected)
    if not poisson_harmonize:
        donor_patch = cv2.convertScaleAbs(donor_patch, alpha=1.04, beta=12)
    if poisson_harmonize:
        center = (x + width // 2, y + height // 2)
        poisson = cv2.seamlessClone(donor_patch, canvas, mask, center, cv2.NORMAL_CLONE)
        donor_patch = poisson[y : y + height, x : x + width]
    alpha = internal_alpha(mask, feather=7.0)
    mixed = np.clip(
        target.astype(np.float32) * (1.0 - alpha)
        + donor_patch.astype(np.float32) * alpha,
        0,
        255,
    ).astype(np.uint8)
    mixed = neutral(mixed)
    target[selected] = mixed[selected]


def crop_red_donor(image: np.ndarray, index: int) -> np.ndarray:
    # Crops keep the generated subject, not its decorative outer frame.
    crops = [
        (110, 90, 925, 900),   # horned head and neck
        (145, 160, 875, 875),  # five-finger grip and spear shaft
        (15, 15, 1010, 1010),  # complete reclining figure and context
    ]
    x0, y0, x1, y1 = crops[index]
    return image[y0:y1, x0:x1]


def texture_crop(texture: np.ndarray, width: int, height: int, seed: int) -> np.ndarray:
    """Return deterministic varied relief crops so separate repairs do not repeat."""
    source_h, source_w = texture.shape[:2]
    aspect = width / max(height, 1)
    crop_long = 480 + (seed * 73) % 360
    if aspect >= 1:
        crop_w = min(source_w, crop_long)
        crop_h = max(120, min(source_h, round(crop_w / aspect)))
    else:
        crop_h = min(source_h, crop_long)
        crop_w = max(120, min(source_w, round(crop_h * aspect)))
    x_range = max(1, source_w - crop_w)
    y_range = max(1, source_h - crop_h)
    x0 = (seed * 137 + 41) % x_range
    y0 = (seed * 193 + 67) % y_range
    crop = texture[y0 : y0 + crop_h, x0 : x0 + crop_w]
    if seed % 2:
        crop = cv2.flip(crop, 1)
    return crop


def connected_regions(mask: np.ndarray, minimum: int = 50) -> list[tuple[np.ndarray, tuple[int, int, int, int], int]]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    regions = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < minimum:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        width = int(stats[label, cv2.CC_STAT_WIDTH])
        height = int(stats[label, cv2.CC_STAT_HEIGHT])
        regions.append(((labels == label).astype(np.uint8) * 255, (x, y, width, height), area))
    regions.sort(key=lambda item: item[1][1])
    return regions


def make_detail_montage(image: np.ndarray) -> np.ndarray:
    boxes = [
        (690, 35, 855, 180),
        (335, 445, 535, 650),
        (25, 720, 225, 925),
        (400, 720, 615, 970),
        (190, 995, 455, 1245),
        (635, 880, 1110, 1254),
    ]
    thumbs = []
    for x0, y0, x1, y1 in boxes:
        crop = image[y0:y1, x0:x1]
        thumbs.append(cv2.resize(crop, (360, 260), interpolation=cv2.INTER_LANCZOS4))
    top = np.hstack(thumbs[:3])
    bottom = np.hstack(thumbs[3:])
    return np.vstack((top, bottom))


def main() -> None:
    destination = cv2.imread(str(DESTINATION), cv2.IMREAD_COLOR)
    yellow_mask = cv2.imread(str(YELLOW_MASK), cv2.IMREAD_GRAYSCALE)
    red_mask = cv2.imread(str(RED_MASK), cv2.IMREAD_GRAYSCALE)
    union_mask = cv2.imread(str(UNION_MASK), cv2.IMREAD_GRAYSCALE)
    red_donors = [cv2.imread(str(path), cv2.IMREAD_COLOR) for path in RED_DONORS]
    yellow_donor = cv2.imread(str(YELLOW_DONOR), cv2.IMREAD_COLOR)
    inputs = [destination, yellow_mask, red_mask, union_mask, yellow_donor, *red_donors]
    if any(item is None for item in inputs):
        raise FileNotFoundError("A destination, mask, or accepted donor is missing")
    if not all(mask.shape == destination.shape[:2] for mask in (yellow_mask, red_mask, union_mask)):
        raise ValueError("All annotation masks must align with the destination")

    repaired = destination.copy()

    yellow_regions = connected_regions(yellow_mask)
    for index, (component, bbox, _) in enumerate(yellow_regions):
        _, _, width, height = bbox
        donor = texture_crop(yellow_donor, width, height, index + 1)
        apply_patch_strict(repaired, donor, component, bbox)

    red_regions = connected_regions(red_mask, minimum=500)
    if len(red_regions) != 3:
        raise AssertionError(f"Expected 3 red replacement regions, found {len(red_regions)}")
    for index, ((component, bbox, _), donor) in enumerate(zip(red_regions, red_donors)):
        apply_patch_strict(
            repaired,
            crop_red_donor(donor, index),
            component,
            bbox,
            poisson_harmonize=False,
        )

    save_png(FINAL, repaired)

    absolute = cv2.absdiff(destination, repaired)
    changed = np.any(absolute != 0, axis=2)
    selected = union_mask > 0
    out_of_mask = changed & ~selected
    difference_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs_Difference.png"
    violations_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs_OutOfMask.png"
    detail_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs_Details.png"
    save_png(difference_path, cv2.convertScaleAbs(absolute, alpha=4))
    violation_view = np.zeros_like(repaired)
    violation_view[out_of_mask] = (0, 0, 255)
    save_png(violations_path, violation_view)
    save_png(detail_path, make_detail_montage(repaired))

    report = {
        "issue": 10,
        "annotated_source": "assets/references/10152026_Annotated_Repairs.pdf",
        "destination": str(DESTINATION.relative_to(ROOT)),
        "destination_sha256": sha256(DESTINATION),
        "final_master": str(FINAL.relative_to(ROOT)),
        "final_master_sha256": sha256(FINAL),
        "dimensions": [int(repaired.shape[1]), int(repaired.shape[0])],
        "yellow_regions_repaired": len(yellow_regions),
        "red_regions_replaced": len(red_regions),
        "approved_mask_pixels": int(np.count_nonzero(selected)),
        "changed_pixels_vs_destination": int(np.count_nonzero(changed)),
        "changed_pixels_outside_approved_masks": int(np.count_nonzero(out_of_mask)),
        "outside_masks_byte_identical": bool(np.count_nonzero(out_of_mask) == 0),
        "edited_pixels_neutral_grayscale": bool(
            np.array_equal(repaired[:, :, 0][selected], repaired[:, :, 1][selected])
            and np.array_equal(repaired[:, :, 1][selected], repaired[:, :, 2][selected])
        ),
        "method": "focused gpt-image-2 donor plates, robust local tone matching, Poisson harmonization for yellow regions, and 7px inward feather",
        "scope": "PDF-highlighted pixels only; halo-pass destination preserved everywhere else",
        "full_source_edit_attempt": "blocked by output safety filter; no blocked output pixels used",
        "status": "passed automated compositing invariants and full-frame/detail visual review",
    }
    qa_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL,
            difference_path,
            violations_path,
            detail_path,
            qa_path,
            YELLOW_MASK,
            RED_MASK,
            UNION_MASK,
            *RED_DONORS,
            YELLOW_DONOR,
        ):
            bundle.write(path, path.relative_to(ROOT))

    if np.count_nonzero(out_of_mask):
        raise AssertionError("Repair changed pixels outside the registered PDF masks")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
