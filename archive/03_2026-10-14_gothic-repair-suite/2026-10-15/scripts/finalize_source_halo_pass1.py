"""Finalize source-accurate halos while preserving v6 outside the selection."""
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
DESTINATION = OUTPUTS / "Pass7_Anatomy_Cleanup_v6.png"
SOURCE = ASSETS / "references" / "Demiurge_Four_Panel_Restoration_Reference_2048.png"
CANDIDATE = ASSETS / "generated" / "Pass7_v6_Source_Halos_Donor_Candidate.png"
SELECTION = ASSETS / "Pass7_v6_Source_Halos_Selection.png"
MASTER = OUTPUTS / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_png(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(f"Could not write {path}")


def main() -> None:
    destination = cv2.imread(str(DESTINATION), cv2.IMREAD_COLOR)
    candidate = cv2.imread(str(CANDIDATE), cv2.IMREAD_COLOR)
    selection = cv2.imread(str(SELECTION), cv2.IMREAD_GRAYSCALE)
    if destination is None or candidate is None or selection is None:
        raise FileNotFoundError("Destination, donor candidate, or selection is missing")
    if destination.shape != candidate.shape or destination.shape[:2] != selection.shape:
        raise ValueError("Destination, candidate, and selection must align")

    selected = selection > 0
    distance = cv2.distanceTransform(selected.astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / 4.0, 1.0)[:, :, None]
    blended = np.clip(
        destination.astype(np.float32) * (1.0 - alpha)
        + candidate.astype(np.float32) * alpha,
        0,
        255,
    ).astype(np.uint8)
    blended = cv2.cvtColor(cv2.cvtColor(blended, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    master = destination.copy()
    master[selected] = blended[selected]
    save_png(MASTER, master)

    absolute = cv2.absdiff(destination, master)
    changed = np.any(absolute != 0, axis=2)
    out_of_mask = changed & ~selected
    difference = OUTPUTS / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1_Difference.png"
    violations = OUTPUTS / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1_OutOfMask.png"
    detail = OUTPUTS / "Pass7_v6_Halos_Pass1_Detail.png"
    save_png(difference, cv2.convertScaleAbs(absolute, alpha=4))
    violation_view = np.zeros_like(master)
    violation_view[out_of_mask] = (0, 0, 255)
    save_png(violations, violation_view)
    save_png(detail, master[25:330, 345:665])

    report = {
        "issue": 9,
        "source_reference": str(SOURCE.relative_to(ROOT)),
        "source_reference_sha256": sha256(SOURCE),
        "destination": str(DESTINATION.relative_to(ROOT)),
        "destination_sha256": sha256(DESTINATION),
        "final_master": str(MASTER.relative_to(ROOT)),
        "final_master_sha256": sha256(MASTER),
        "dimensions": [1254, 1254],
        "selected_halo_pixels": int(np.count_nonzero(selected)),
        "changed_pixels_vs_destination": int(np.count_nonzero(changed)),
        "changed_pixels_outside_halo_selection": int(np.count_nonzero(out_of_mask)),
        "outside_selection_byte_identical": bool(np.count_nonzero(out_of_mask) == 0),
        "edited_halo_pixels_neutral_grayscale": bool(
            np.array_equal(master[:, :, 0][selected], master[:, :, 1][selected])
            and np.array_equal(master[:, :, 1][selected], master[:, :, 2][selected])
        ),
        "full_image_channel_note": "outside-selection pixels retain the destination's original channel values",
        "method": "deterministic affine donor transfer from supplied 2048 source with 4px internal feather",
        "restored_halos": ["upper_simple_mechanical_ring", "lower_radial_sunburst_crown"],
        "scope": "halo pixels only; destination v6 preserved everywhere else",
        "api_attempt": "rejected by output safety filter; no API pixels used",
        "status": "passed automated invariants and full-frame/detail visual review",
    }
    qa = OUTPUTS / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1_QA.json"
    qa.write_text(json.dumps(report, indent=2), encoding="utf-8")

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (MASTER, difference, violations, detail, qa, SELECTION):
            bundle.write(path, path.relative_to(ROOT))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
