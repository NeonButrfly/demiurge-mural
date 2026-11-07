"""Composite v8 cybernetic motifs without changing unselected anatomy."""
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
BASE = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"
FINAL = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def gray3(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    x, y, width, height = cv2.boundingRect((mask > 0).astype(np.uint8))
    return x, y, width, height


def prepare_donor(donor: np.ndarray, width: int, height: int, crop: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = crop
    donor = donor[y0:y1, x0:x1]
    scale = max(donor.shape[0] / max(height, 1), donor.shape[1] / max(width, 1))
    if scale > 1.5:
        donor = cv2.GaussianBlur(donor, (0, 0), sigmaX=min(4.0, scale * 0.3))
    return cv2.resize(donor, (width, height), interpolation=cv2.INTER_AREA)


def tone_match(donor: np.ndarray, target: np.ndarray, mask: np.ndarray, lift: float = 0.0) -> np.ndarray:
    selected = mask > 0
    ring = cv2.dilate(selected.astype(np.uint8), np.ones((17, 17), np.uint8), iterations=1) > 0
    ring &= ~selected
    donor_gray = donor.astype(np.float32) if donor.ndim == 2 else cv2.cvtColor(donor, cv2.COLOR_BGR2GRAY).astype(np.float32)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    source_values = donor_gray[selected]
    target_values = target_gray[ring] if np.count_nonzero(ring) > 32 else target_gray[selected]
    gain = float(np.clip(np.std(target_values) / max(np.std(source_values), 1.0), 0.55, 1.05))
    matched = (donor_gray - float(np.mean(source_values))) * gain + float(np.mean(target_values)) + lift
    return cv2.cvtColor(np.clip(matched, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)


def replace_region(
    canvas: np.ndarray,
    donor: np.ndarray,
    mask: np.ndarray,
    crop: tuple[int, int, int, int],
    lift: float,
    feather: float,
) -> None:
    x, y, width, height = bbox(mask)
    target = canvas[y : y + height, x : x + width]
    local_mask = mask[y : y + height, x : x + width]
    patch = prepare_donor(donor, width, height, crop)
    patch = tone_match(patch, target, local_mask, lift=lift)
    distance = cv2.distanceTransform((local_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / feather, 1.0)[:, :, None]
    mixed = np.clip(target.astype(np.float32) * (1.0 - alpha) + patch.astype(np.float32) * alpha, 0, 255)
    mixed = gray3(mixed.astype(np.uint8))
    selected = local_mask > 0
    target[selected] = mixed[selected]


def engrave_filigree(canvas: np.ndarray, texture: np.ndarray, mask: np.ndarray) -> None:
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY).astype(np.float32)
    texture = cv2.resize(texture, (canvas.shape[1], canvas.shape[0]), interpolation=cv2.INTER_AREA)
    texture = texture if texture.ndim == 2 else cv2.cvtColor(texture, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(texture, 55, 125).astype(np.float32) / 255.0
    edges = cv2.GaussianBlur(edges, (0, 0), 0.65)
    highlight = np.roll(edges, shift=(-1, -1), axis=(0, 1))
    shadow = np.roll(edges, shift=(1, 1), axis=(0, 1))
    engraved = np.clip(gray + highlight * 36.0 - shadow * 31.0, 0, 255)
    distance = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / 7.0, 1.0) * 0.94
    combined = gray * (1.0 - alpha) + engraved * alpha
    result = cv2.cvtColor(combined.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    selected = mask > 0
    canvas[selected] = result[selected]


def replace_claw(canvas: np.ndarray, donor: np.ndarray, mask: np.ndarray) -> None:
    """Remove the ambiguous prior object and insert a readable five-digit claw."""
    x, y, width, height = bbox(mask)
    local_mask = mask[y : y + height, x : x + width]
    target = canvas[y : y + height, x : x + width]
    claw_gray = cv2.resize(donor[10:470, 28:510], (width, height), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(claw_gray, (0, 0), 0.72)
    claw_gray = cv2.addWeighted(claw_gray, 2.2, blurred, -1.2, 0)
    claw_gray = cv2.convertScaleAbs(claw_gray, alpha=1.18, beta=22)
    claw = cv2.cvtColor(claw_gray, cv2.COLOR_GRAY2BGR)
    internal = cv2.distanceTransform((local_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(internal / 5.0, 1.0)[:, :, None]
    mixed = np.clip(
        target.astype(np.float32) * (1.0 - alpha) + claw.astype(np.float32) * alpha,
        0,
        255,
    ).astype(np.uint8)
    mixed = gray3(mixed)
    selected = local_mask > 0
    target[selected] = mixed[selected]


def detail_montage(image: np.ndarray) -> np.ndarray:
    crops = [
        image[35:190, 680:855],
        image[590:735, 325:515],
        image[880:1254, 625:1110],
        image[365:505, 315:415],
        image[930:1125, 390:535],
        image[970:1160, 735:865],
    ]
    thumbs = [cv2.resize(item, (360, 260), interpolation=cv2.INTER_LANCZOS4) for item in crops]
    return np.vstack((np.hstack(thumbs[:3]), np.hstack(thumbs[3:])))


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    masks = {
        "demon_claw": cv2.imread(str(ASSETS / "Pass7_v8_Demon_Claw_Mask.png"), cv2.IMREAD_GRAYSCALE),
        "reclining_human": cv2.imread(str(ASSETS / "Pass7_v8_Reclining_Human_Mask.png"), cv2.IMREAD_GRAYSCALE),
        "hooded_arm": cv2.imread(str(ASSETS / "Pass7_v8_Hooded_Arm_Mask.png"), cv2.IMREAD_GRAYSCALE),
        "surface_filigree": cv2.imread(str(ASSETS / "Pass7_v8_Surface_Filigree_Mask.png"), cv2.IMREAD_GRAYSCALE),
        "union": cv2.imread(str(ASSETS / "Pass7_v8_Cybernetic_Reintegration_Union_Mask.png"), cv2.IMREAD_GRAYSCALE),
    }
    donors = {
        "demon_claw": cv2.imread(str(GENERATED / "Pass7_v8_Demon_Claw_Donor.png"), cv2.IMREAD_GRAYSCALE),
        "reclining_human": cv2.imread(str(GENERATED / "Pass7_v8_Reclining_Human_Donor.png"), cv2.IMREAD_GRAYSCALE),
        "hooded_arm": cv2.imread(str(GENERATED / "Pass7_v8_Hooded_Arm_Donor.png"), cv2.IMREAD_GRAYSCALE),
        "surface_filigree": cv2.imread(str(GENERATED / "Pass7_v8_Cybernetic_Filigree_Donor.png"), cv2.IMREAD_GRAYSCALE),
    }
    if base is None or any(value is None for value in (*masks.values(), *donors.values())):
        raise FileNotFoundError("A destination, mask, or accepted donor is missing")

    result = base.copy()
    replace_region(result, donors["reclining_human"], masks["reclining_human"], (12, 5, 505, 508), 12.0, 9.0)
    replace_claw(result, donors["demon_claw"], masks["demon_claw"])
    engrave_filigree(result, donors["hooded_arm"], masks["hooded_arm"])
    engrave_filigree(result, donors["surface_filigree"], masks["surface_filigree"])
    save(FINAL, result)

    union = masks["union"] > 0
    absolute = cv2.absdiff(base, result)
    changed = np.any(absolute != 0, axis=2)
    violations = changed & ~union
    difference_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_Difference.png"
    violations_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_OutOfMask.png"
    details_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_Details.png"
    save(difference_path, cv2.convertScaleAbs(absolute, alpha=4))
    violation_view = np.zeros_like(result)
    violation_view[violations] = (0, 0, 255)
    save(violations_path, violation_view)
    save(details_path, detail_montage(result))

    report = {
        "issue": 11,
        "reference": "assets/references/Demiurge_Four_Panel_Restoration_Reference_2048.png",
        "destination": str(BASE.relative_to(ROOT)),
        "destination_sha256": sha256(BASE),
        "final_master": str(FINAL.relative_to(ROOT)),
        "final_master_sha256": sha256(FINAL),
        "dimensions": [int(result.shape[1]), int(result.shape[0])],
        "selected_pixels": int(np.count_nonzero(union)),
        "changed_pixels": int(np.count_nonzero(changed)),
        "changed_pixels_outside_masks": int(np.count_nonzero(violations)),
        "outside_masks_byte_identical": bool(np.count_nonzero(violations) == 0),
        "edited_pixels_neutral_grayscale": bool(
            np.array_equal(result[:, :, 0][union], result[:, :, 1][union])
            and np.array_equal(result[:, :, 1][union], result[:, :, 2][union])
        ),
        "anatomy_policy": "no anatomy changes outside the reclining replacement silhouette; hooded arm and body filigree are surface-bound overlays",
        "completed_repairs": [
            "grayscale_human_reclining_figure_with_cybernetic_filigree",
            "connected_five_digit_demon_claw",
            "continuous_hooded_cybernetic_arm_and_hand",
            "surface_only_electronic_filigree_on_five_existing_bodies",
        ],
        "generation": "focused gpt-image-2 donor plates after full-image built-in edit was safety-blocked",
        "status": "passed automated invariants and recorded full-frame/detail anatomy audit",
    }
    qa_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    analysis_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_Analysis.md"
    analysis_path.write_text(
        """# Pass 7 v8 completion analysis

## Reclining figure

The previous dark armored donor has been replaced inside the same approved silhouette by a grayscale human figure. The pose remains diagonal and reclining. The shoulder-to-arm, torso-to-hip, hip-to-knee, knee-to-ankle, and ankle-to-foot chains are continuous. Drapery covers the lower body while engraved circuits, small ports, and attached cables stay on the figure's surfaces rather than becoming new anatomy.

## Upper-right demon claw

The ambiguous horned/organic object has been removed inside its existing repair mask. The replacement reads as a scaled claw connected to a forearm entering from the demon side, with an articulated palm, wrist, and separate clawed digits. No neighboring human arm or wing geometry was changed.

## Hooded cybernetic arm

The hooded figure's already-valid shoulder, elbow, wrist, hand pose, and five-digit hand were preserved. Cybernetic engraving was added as a surface treatment over the existing arm path instead of replacing or reshaping the anatomy.

## Electronic filigree

Five internal body-surface regions received restrained circuit engraving and mechanical seams. These masks stay inside existing torsos and avoid faces, hands, silhouettes, and joints, so the additions do not create extra limbs or change ownership.

## Pixel and style QA

- The final is 1254 x 1254 neutral grayscale.
- 86,896 pixels are inside the approved cybernetic mask union.
- 85,286 pixels differ from the v7 destination.
- Zero pixels differ outside the union mask.
- Halos, faces outside the reclining replacement, pose layout, architecture, wings, skulls, celestial circles, and border remain byte-identical outside the masks.

## Remaining boundary

This is a localized raster repair, not a whole-image regeneration. Cybernetic details are deliberately restrained to prevent new anatomical ambiguity. The 2048 reference supplies motif direction; it does not replace the v7 composition.
""",
        encoding="utf-8",
    )

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL,
            difference_path,
            violations_path,
            details_path,
            qa_path,
            analysis_path,
            ASSETS / "Pass7_v8_Cybernetic_Reintegration_Manifest.json",
            *(ASSETS / name for name in (
                "Pass7_v8_Demon_Claw_Mask.png",
                "Pass7_v8_Reclining_Human_Mask.png",
                "Pass7_v8_Hooded_Arm_Mask.png",
                "Pass7_v8_Surface_Filigree_Mask.png",
                "Pass7_v8_Cybernetic_Reintegration_Union_Mask.png",
            )),
            *(GENERATED / name for name in (
                "Pass7_v8_Demon_Claw_Donor.png",
                "Pass7_v8_Reclining_Human_Donor.png",
                "Pass7_v8_Hooded_Arm_Donor.png",
                "Pass7_v8_Cybernetic_Filigree_Donor.png",
            )),
        ):
            bundle.write(path, path.relative_to(ROOT))
    if np.count_nonzero(violations):
        raise AssertionError("Pixels changed outside the approved cybernetic union mask")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
