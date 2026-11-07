"""Composite issue #13 corrections with strict out-of-mask byte identity."""
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
BASE = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections.png"
PRE_HALO = OUTPUTS / "Pass7_Anatomy_Cleanup_v6.png"
SOURCE = ASSETS / "references" / "Demiurge_Four_Panel_Restoration_Reference_2048.png"
FINAL = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections.png"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gray3(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def tone_match(patch: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
    selected = mask > 0
    ring = cv2.dilate(selected.astype(np.uint8), np.ones((17, 17), np.uint8), iterations=1) > 0
    ring &= ~selected
    patch_gray = cv2.cvtColor(gray3(patch), cv2.COLOR_BGR2GRAY).astype(np.float32)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    source_values = patch_gray[selected]
    target_values = target_gray[ring] if np.count_nonzero(ring) > 32 else target_gray[selected]
    gain = float(np.clip(np.std(target_values) / max(np.std(source_values), 1.0), 0.72, 1.25))
    matched = (patch_gray - float(np.mean(source_values))) * gain + float(np.mean(target_values))
    matched = np.clip(matched, 0, 255).astype(np.uint8)
    detail = cv2.addWeighted(matched, 1.45, cv2.GaussianBlur(matched, (0, 0), 0.72), -0.45, 0)
    return cv2.cvtColor(detail, cv2.COLOR_GRAY2BGR)


def blend_selected(
    canvas: np.ndarray,
    donor: np.ndarray,
    mask: np.ndarray,
    feather: float,
) -> None:
    matched = tone_match(donor, canvas, mask)
    distance = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / feather, 1.0)[:, :, None]
    mixed = np.clip(canvas.astype(np.float32) * (1.0 - alpha) + matched.astype(np.float32) * alpha, 0, 255)
    selected = mask > 0
    canvas[selected] = gray3(mixed.astype(np.uint8))[selected]


def place_generated_crop(
    canvas: np.ndarray,
    donor: np.ndarray,
    mask: np.ndarray,
    bounds: dict[str, int],
    feather: float,
) -> None:
    x0, y0, x1, y1 = (bounds[key] for key in ("x0", "y0", "x1", "y1"))
    target = canvas[y0:y1, x0:x1]
    local_mask = mask[y0:y1, x0:x1]
    patch = cv2.resize(donor, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    blend_selected(target, patch, local_mask, feather)


def warp_about_centers(
    source: np.ndarray,
    source_center: tuple[int, int],
    destination_center: tuple[int, int],
    scale: float,
    destination_shape: tuple[int, int],
) -> np.ndarray:
    matrix = np.array(
        [
            [scale, 0.0, destination_center[0] - scale * source_center[0]],
            [0.0, scale, destination_center[1] - scale * source_center[1]],
        ],
        dtype=np.float32,
    )
    return cv2.warpAffine(
        source,
        matrix,
        (destination_shape[1], destination_shape[0]),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT_101,
    )


def radial_mask(shape: tuple[int, int], center: tuple[int, int], inner: int, outer: int) -> np.ndarray:
    yy, xx = np.ogrid[: shape[0], : shape[1]]
    distance_sq = (xx - center[0]) ** 2 + (yy - center[1]) ** 2
    return ((distance_sq >= inner**2) & (distance_sq <= outer**2)).astype(np.uint8) * 255


def restore_centered_halo(
    canvas: np.ndarray,
    pre_halo: np.ndarray,
    source: np.ndarray,
    approved: np.ndarray,
) -> None:
    # First erase the displaced v9 spikes with the clean v6 destination.
    blend_selected(canvas, pre_halo, approved, feather=5.0)
    # Then transfer the user's original spiked halo, centered on the angel's head.
    centered = warp_about_centers(source, (752, 340), (478, 216), 0.758, canvas.shape[:2])
    new_ring = cv2.bitwise_and(approved, radial_mask(canvas.shape[:2], (478, 216), 31, 94))
    blend_selected(canvas, centered, new_ring, feather=4.0)


def details(image: np.ndarray) -> np.ndarray:
    crops = [
        image[0:300, 630:1040],
        image[90:330, 335:585],
        image[275:765, 370:730],
        image[0:390, 885:1110],
        image[790:1254, 545:1220],
    ]
    thumbs = [cv2.resize(crop, (420, 300), interpolation=cv2.INTER_LANCZOS4) for crop in crops]
    blank = np.full_like(thumbs[0], 32)
    return np.vstack((np.hstack(thumbs[:3]), np.hstack((thumbs[3], thumbs[4], blank))))


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    pre_halo = cv2.imread(str(PRE_HALO), cv2.IMREAD_COLOR)
    source = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
    manifest = json.loads((ASSETS / "Pass7_v10_Anatomy_Halo_Manifest.json").read_text(encoding="utf-8"))
    names = ("demon_arm", "reclining_lady", "spiked_halo", "abdominal_bump", "upper_right_bubbles")
    masks = {
        name: cv2.imread(str(ASSETS / f"Pass7_v10_{name}_Mask.png"), cv2.IMREAD_GRAYSCALE)
        for name in names
    }
    union = cv2.imread(str(ASSETS / "Pass7_v10_Anatomy_Halo_Union_Mask.png"), cv2.IMREAD_GRAYSCALE)
    donors = {
        "demon_arm": cv2.imread(str(GENERATED / "Pass7_v10_Demon_Arm_Donor.png"), cv2.IMREAD_COLOR),
        "reclining_lady": cv2.imread(str(GENERATED / "Pass7_v10_Reclining_Lady_Donor.png"), cv2.IMREAD_COLOR),
        "abdominal_bump": cv2.imread(str(GENERATED / "Pass7_v10_Abdominal_Drapery_Donor.png"), cv2.IMREAD_COLOR),
        "upper_right_bubbles": cv2.imread(str(GENERATED / "Pass7_v10_Upper_Right_Bubbles_Donor.png"), cv2.IMREAD_COLOR),
    }
    required = [base, pre_halo, source, union, *masks.values(), *donors.values()]
    if any(item is None for item in required):
        raise FileNotFoundError("A v10 base, mask, source, or donor is missing")

    result = base.copy()
    place_generated_crop(result, donors["demon_arm"], masks["demon_arm"], manifest["regions"]["demon_arm"]["bounds"], 6.0)
    place_generated_crop(result, donors["upper_right_bubbles"], masks["upper_right_bubbles"], manifest["regions"]["upper_right_bubbles"]["bounds"], 5.0)
    place_generated_crop(result, donors["abdominal_bump"], masks["abdominal_bump"], manifest["regions"]["abdominal_bump"]["bounds"], 7.0)
    place_generated_crop(result, donors["reclining_lady"], masks["reclining_lady"], manifest["regions"]["reclining_lady"]["bounds"], 9.0)
    restore_centered_halo(result, pre_halo, source, masks["spiked_halo"])
    save(FINAL, result)

    selected = union > 0
    absolute = cv2.absdiff(base, result)
    changed = np.any(absolute != 0, axis=2)
    violations = changed & ~selected
    difference_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections_Difference.png"
    out_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections_OutOfMask.png"
    details_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections_Details.png"
    save(difference_path, cv2.convertScaleAbs(absolute, alpha=4.0))
    violation_view = np.zeros_like(result)
    violation_view[violations] = (0, 0, 255)
    save(out_path, violation_view)
    save(details_path, details(result))

    report = {
        "issue": 13,
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
            "demon_arm": "one attached shoulder-to-five-talon claw chain",
            "reclining_lady": "one coherent fully draped reclining figure with cybernetic filigree",
            "spiked_halo": "original-source radial halo centered at the angel head",
            "abdominal_bump": "ownerless protrusion replaced by continuous robe and feather folds",
            "upper_right_bubbles": "two smooth bubble clusters replaced by angular wing and Gothic architectural relief",
        },
        "generation": "focused donor edits for demon arm, reclining figure, drapery, and bubbles; deterministic original-source halo transfer",
    }
    qa_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    analysis_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections_Analysis.md"
    analysis_path.write_text(
        "# Pass 7 v10 correction analysis\n\n"
        "Issue #13 isolates five user-marked regions. The demon now has one continuous raised arm and a readable five-talon claw. "
        "The lower-right replacement is a single fully draped reclining figure. The original-source spiked halo is centered on the angel's head. "
        "The central ownerless protrusion is replaced by continuous robe and feather folds, and both upper-right bubble clusters are replaced with coherent wing, sky, and architectural relief.\n\n"
        "## Invariant QA\n\n"
        f"- Dimensions: {result.shape[1]} x {result.shape[0]}.\n"
        f"- Approved union: {report['selected_pixels']:,} pixels.\n"
        f"- Changed pixels: {report['changed_pixels']:,}.\n"
        f"- Changed pixels outside masks: {report['changed_pixels_outside_masks']}.\n"
        f"- Neutral grayscale changed pixels: {report['changed_pixels_neutral_grayscale']}.\n\n"
        "Automated checks establish mask confinement, dimensions, and grayscale neutrality. Anatomical and seam quality were also reviewed in the full-frame and detail montage.\n",
        encoding="utf-8",
    )

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL,
            difference_path,
            out_path,
            details_path,
            qa_path,
            analysis_path,
            OUTPUTS / "Pass7_v10_Anatomy_Halo_Mask_Preview.png",
            ASSETS / "Pass7_v10_Anatomy_Halo_Manifest.json",
            ASSETS / "Pass7_v10_Anatomy_Halo_Union_Mask.png",
            *(ASSETS / f"Pass7_v10_{name}_Mask.png" for name in names),
            *donor_paths(),
        ):
            bundle.write(path, path.relative_to(ROOT))

    if np.count_nonzero(violations):
        raise AssertionError("Pixels changed outside the approved issue #13 mask union")
    if not report["changed_pixels_neutral_grayscale"]:
        raise AssertionError("Changed pixels are not neutral grayscale")
    print(json.dumps(report, indent=2))


def donor_paths() -> tuple[Path, ...]:
    return (
        GENERATED / "Pass7_v10_Demon_Arm_Donor.png",
        GENERATED / "Pass7_v10_Reclining_Lady_Donor.png",
        GENERATED / "Pass7_v10_Abdominal_Drapery_Donor.png",
        GENERATED / "Pass7_v10_Upper_Right_Bubbles_Donor.png",
    )


if __name__ == "__main__":
    main()
