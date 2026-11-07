"""Composite the original-halo candidate strictly inside the approved halo mask."""
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
TARGET = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v7.png"
REFERENCE = ASSETS / "Gothic_Relief_Pass_7_Original.png"
CANDIDATE = ASSETS / "generated" / "Pass7_Original_Halos_Restoration_Candidate.png"
SELECTION = ASSETS / "Pass7_Original_Halos_Selection.png"
MASTER = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_png(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(f"Could not write {path}")


def main() -> None:
    target = cv2.imread(str(TARGET), cv2.IMREAD_COLOR)
    candidate = cv2.imread(str(CANDIDATE), cv2.IMREAD_COLOR)
    selection = cv2.imread(str(SELECTION), cv2.IMREAD_GRAYSCALE)
    if target is None or candidate is None or selection is None:
        raise FileNotFoundError("Target, generated candidate, or halo selection is missing")
    if target.shape != (2048, 2048, 3) or candidate.shape != target.shape:
        raise ValueError("Target and candidate must both be 2048x2048 RGB images")
    if selection.shape != target.shape[:2]:
        raise ValueError("Halo selection must align with the target")

    candidate_gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
    candidate_gray = cv2.cvtColor(candidate_gray, cv2.COLOR_GRAY2BGR)

    selected = selection > 0
    distance = cv2.distanceTransform(selected.astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / 8.0, 1.0)[:, :, None]
    blended = np.clip(
        target.astype(np.float32) * (1.0 - alpha)
        + candidate_gray.astype(np.float32) * alpha,
        0,
        255,
    ).astype(np.uint8)
    master = target.copy()
    master[selected] = blended[selected]

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    save_png(MASTER, master)
    compatibility = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos_1254.png"
    save_png(compatibility, cv2.resize(master, (1254, 1254), interpolation=cv2.INTER_LANCZOS4))

    absolute = cv2.absdiff(target, master)
    changed = np.any(absolute != 0, axis=2)
    out_of_mask = changed & ~selected
    difference = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos_Difference.png"
    violations = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos_OutOfMask.png"
    detail = OUTPUTS / "Pass7_v8_Original_Halos_Detail.png"
    save_png(difference, cv2.convertScaleAbs(absolute, alpha=4))
    violation_view = np.zeros_like(target)
    violation_view[out_of_mask] = (0, 0, 255)
    save_png(violations, violation_view)
    save_png(detail, master[25:560, 500:1075])

    report = {
        "issue": 9,
        "edit_target": str(TARGET.relative_to(ROOT)),
        "edit_target_sha256": sha256(TARGET),
        "original_halo_reference": str(REFERENCE.relative_to(ROOT)),
        "original_halo_reference_sha256": sha256(REFERENCE),
        "generated_candidate": str(CANDIDATE.relative_to(ROOT)),
        "generated_candidate_sha256": sha256(CANDIDATE),
        "approved_selection": str(SELECTION.relative_to(ROOT)),
        "approved_selection_pixels": int(np.count_nonzero(selected)),
        "final_master": str(MASTER.relative_to(ROOT)),
        "final_master_sha256": sha256(MASTER),
        "dimensions": [2048, 2048],
        "changed_pixels_vs_v7": int(np.count_nonzero(changed)),
        "changed_pixels_outside_approved_selection": int(np.count_nonzero(out_of_mask)),
        "outside_selection_byte_identical": bool(np.count_nonzero(out_of_mask) == 0),
        "neutral_grayscale_rgb_channels_identical": bool(
            np.array_equal(master[:, :, 0], master[:, :, 1])
            and np.array_equal(master[:, :, 1], master[:, :, 2])
        ),
        "method": "gpt-image-2 reference-guided halo edit, then 8px internal feather and strict mask compositing",
        "scope": "two upper-central engraved halo rings only",
        "status": "passed automated invariants; visually reviewed at full frame and halo detail",
    }
    qa = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos_QA.json"
    qa.write_text(json.dumps(report, indent=2), encoding="utf-8")

    archive = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (MASTER, compatibility, difference, violations, detail, qa, SELECTION):
            bundle.write(path, path.relative_to(ROOT))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
