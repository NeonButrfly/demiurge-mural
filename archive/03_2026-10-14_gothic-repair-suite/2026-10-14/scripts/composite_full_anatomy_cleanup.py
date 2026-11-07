"""Composite the approved manual reclining-figure repair with strict QA."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import out_of_mask_diff, strict_alpha_composite


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
WORK = ROOT / "work" / "full_anatomy_cleanup"
ORIGINAL = ASSETS / "Gothic_Relief_Pass_7_Original.png"
BASE = OUTPUTS / "Pass7_Anatomy_Repairs_v2.png"
OUTPUT = OUTPUTS / "Pass7_Anatomy_Cleanup_v3.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    original = cv2.imread(str(ORIGINAL), cv2.IMREAD_COLOR)
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    candidate = cv2.imread(str(WORK / "reclining_hip_legs_manual_candidate.png"), cv2.IMREAD_COLOR)
    new_mask = cv2.imread(str(ASSETS / "Pass7_Reclining_Hip_Legs_Mask.png"), cv2.IMREAD_GRAYSCALE)
    if any(item is None for item in (original, base, candidate, new_mask)):
        raise FileNotFoundError("A source, candidate, or approved mask is missing")

    x0, y0, x1, y1 = 400, 805, 620, 970
    candidate_full = base.copy()
    candidate_full[y0:y1, x0:x1] = candidate
    repaired = strict_alpha_composite(base, candidate_full, new_mask)

    mask_names = [
        "Pass7_Central_Legs_Inpaint_Mask.png",
        "Pass7_Hooded_Cybernetic_Hand_Mask.png",
        "Pass7_Spear_Grip_Mask.png",
        "Pass7_Reclining_Hip_Legs_Mask.png",
    ]
    union = np.zeros(original.shape[:2], np.uint8)
    for name in mask_names:
        loaded = cv2.imread(str(ASSETS / name), cv2.IMREAD_GRAYSCALE)
        if loaded is None:
            raise FileNotFoundError(ASSETS / name)
        union = cv2.bitwise_or(union, loaded)

    outside, violations = out_of_mask_diff(original, repaired, union)
    if outside:
        raise AssertionError(f"{outside} pixels changed outside approved-mask union")

    cv2.imwrite(str(OUTPUT), repaired, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    difference = cv2.convertScaleAbs(cv2.absdiff(original, repaired), alpha=4)
    cv2.imwrite(str(OUTPUTS / "Pass7_Anatomy_Cleanup_v3_Difference.png"), difference)
    cv2.imwrite(str(OUTPUTS / "Pass7_Anatomy_Cleanup_v3_OutOfMask.png"), violations)
    crop = repaired[y0:y1, x0:x1]
    cv2.imwrite(str(OUTPUTS / "Pass7_Reclining_Hip_Legs_Repair_Crop.png"), crop)
    cv2.imwrite(
        str(OUTPUTS / "Pass7_Reclining_Hip_Legs_Repair_Crop_4x.png"),
        cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
    )

    report = {
        "source_sha256": sha256(ORIGINAL),
        "output_sha256": sha256(OUTPUT),
        "dimensions": [int(repaired.shape[1]), int(repaired.shape[0])],
        "approved_mask_pixels": int(np.count_nonzero(union)),
        "changed_pixels_outside_approved_masks": int(outside),
        "outside_masks_byte_identical": outside == 0,
        "repairs": [
            "central_feet_and_shins",
            "hooded_cybernetic_hand",
            "spear_grip",
            "reclining_hip_and_leg_ownership",
        ],
        "method": "same-artwork donor transform with constrained feather compositing",
        "arm_audit": {
            "reviewed_region": "lower_center_arm_cluster",
            "additional_edit_applied": False,
            "reason": "high-resolution review showed a continuous shoulder-to-hand owner; editing would replace valid anatomy",
        },
        "status": "approved_after_visual_and_invariant_review",
    }
    (OUTPUTS / "Pass7_Anatomy_Cleanup_v3_QA.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
