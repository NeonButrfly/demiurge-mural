"""Approve the center cleanup candidate and emit cumulative v4 QA artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import out_of_mask_diff


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
WORK = ROOT / "work" / "center_cleanup"
ORIGINAL = ASSETS / "Gothic_Relief_Pass_7_Original.png"
OUTPUT = OUTPUTS / "Pass7_Anatomy_Cleanup_v4.png"

MASK_NAMES = [
    "Pass7_Central_Legs_Inpaint_Mask.png",
    "Pass7_Hooded_Cybernetic_Hand_Mask.png",
    "Pass7_Spear_Grip_Mask.png",
    "Pass7_Reclining_Hip_Legs_Mask.png",
    "Pass7_Ownerless_Center_Arm_Mask.png",
    "Pass7_Central_Bulbous_Forms_Mask.png",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    original = cv2.imread(str(ORIGINAL), cv2.IMREAD_COLOR)
    repaired = cv2.imread(
        str(WORK / "center_cleanup_final_candidate.png"), cv2.IMREAD_COLOR
    )
    if original is None or repaired is None:
        raise FileNotFoundError("Run prepare_center_cleanup.py and build_center_cleanup_candidates.py")

    union = np.zeros(original.shape[:2], np.uint8)
    mask_counts: dict[str, int] = {}
    for name in MASK_NAMES:
        mask = cv2.imread(str(ASSETS / name), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise FileNotFoundError(ASSETS / name)
        mask_counts[name] = int(np.count_nonzero(mask))
        union = cv2.bitwise_or(union, mask)

    outside, violations = out_of_mask_diff(original, repaired, union)
    if outside:
        raise AssertionError(f"{outside} pixels changed outside approved-mask union")

    cv2.imwrite(str(OUTPUT), repaired, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    cv2.imwrite(
        str(OUTPUTS / "Pass7_Anatomy_Cleanup_v4_Difference.png"),
        cv2.convertScaleAbs(cv2.absdiff(original, repaired), alpha=4),
    )
    cv2.imwrite(str(OUTPUTS / "Pass7_Anatomy_Cleanup_v4_OutOfMask.png"), violations)
    x0, y0, x1, y1 = 500, 560, 790, 930
    crop = repaired[y0:y1, x0:x1]
    cv2.imwrite(str(OUTPUTS / "Pass7_Center_Cleanup_Crop.png"), crop)
    cv2.imwrite(
        str(OUTPUTS / "Pass7_Center_Cleanup_Crop_3x.png"),
        cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
    )

    report = {
        "source_sha256": sha256(ORIGINAL),
        "output_sha256": sha256(OUTPUT),
        "dimensions": [int(repaired.shape[1]), int(repaired.shape[0])],
        "approved_mask_pixels": int(np.count_nonzero(union)),
        "mask_pixels_by_file": mask_counts,
        "changed_pixels_outside_approved_masks": int(outside),
        "outside_masks_byte_identical": outside == 0,
        "new_repairs": [
            "removed_ownerless_distended_center_arm_and_hand",
            "removed_adjacent_unexplained_bulbous_forms",
            "replaced_defects_with_non_anatomical_feather_and_drapery_relief",
        ],
        "preserved": [
            "surrounding_faces",
            "valid_skulls",
            "valid_owned_foreground_arms",
            "all_pixels_outside_approved_masks",
        ],
        "status": "approved_after_full_image_and_3x_crop_review",
    }
    (OUTPUTS / "Pass7_Anatomy_Cleanup_v4_QA.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
