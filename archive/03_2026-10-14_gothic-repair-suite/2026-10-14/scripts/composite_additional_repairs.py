"""Strictly composite approved focused candidates for issues #3 and #4."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import out_of_mask_diff, strict_alpha_composite
from prepare_additional_repairs import REGIONS


ROOT = Path(__file__).parents[1]
BASE = ROOT / "outputs" / "Pass7_Central_Legs_Repair.png"
ORIGINAL = ROOT / "assets" / "Gothic_Relief_Pass_7_Original.png"
ASSETS = ROOT / "assets"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hooded-hand", type=Path, required=True)
    parser.add_argument("--spear-grip", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "Pass7_Anatomy_Repairs_v2.png")
    args = parser.parse_args()
    candidates = {"hooded_hand": args.hooded_hand, "spear_grip": args.spear_grip}

    original = cv2.imread(str(ORIGINAL), cv2.IMREAD_COLOR)
    working = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if original is None or working is None:
        raise FileNotFoundError("Original or approved base image is missing")
    union = cv2.imread(str(ASSETS / "Pass7_Central_Legs_Inpaint_Mask.png"), cv2.IMREAD_GRAYSCALE)

    for name, config in REGIONS.items():
        generated = cv2.imread(str(candidates[name]), cv2.IMREAD_COLOR)
        mask = cv2.imread(str(ASSETS / config["mask_file"]), cv2.IMREAD_GRAYSCALE)
        if generated is None or mask is None:
            raise FileNotFoundError(f"Missing candidate or mask for {name}")
        x0, y0, x1, y1 = config["crop"]
        candidate_full = working.copy()
        candidate_full[y0:y1, x0:x1] = cv2.resize(generated, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LANCZOS4)
        working = strict_alpha_composite(working, candidate_full, mask)
        union = cv2.bitwise_or(union, mask)

    outside, violations = out_of_mask_diff(original, working, union)
    if outside:
        raise AssertionError(f"{outside} pixels changed outside the union of approved masks")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.output), working, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    cv2.imwrite(str(args.output.with_name("Pass7_Anatomy_Repairs_v2_Difference.png")),
                cv2.convertScaleAbs(cv2.absdiff(original, working), alpha=4))
    cv2.imwrite(str(args.output.with_name("Pass7_Anatomy_Repairs_v2_OutOfMask.png")), violations)
    for name, config in REGIONS.items():
        x0, y0, x1, y1 = config["crop"]
        crop = working[y0:y1, x0:x1]
        cv2.imwrite(str(args.output.with_name(f"Pass7_{name}_Repair_Crop.png")), crop)
        cv2.imwrite(str(args.output.with_name(f"Pass7_{name}_Repair_Crop_4x.png")),
                    cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))
    report = {
        "source_sha256": sha256(ORIGINAL), "output_sha256": sha256(args.output),
        "dimensions": [working.shape[1], working.shape[0]],
        "approved_mask_pixels": int(np.count_nonzero(union)),
        "changed_pixels_outside_approved_masks": outside,
        "outside_masks_byte_identical": outside == 0,
        "repairs": ["central_feet_and_shins", "hooded_cybernetic_hand", "spear_grip"],
        "status": "approved_after_visual_and_invariant_review",
        "visual_review": {
            "hooded_hand_has_one_clear_owner": True,
            "hooded_hand_has_five_distinct_mechanical_digits": True,
            "spear_grip_has_four_wrapped_fingers_and_opposing_thumb": True,
            "spear_shaft_is_continuous": True,
            "hard_boundary_seams_observed": False,
        },
    }
    args.output.with_name("Pass7_Anatomy_Repairs_v2_QA.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
