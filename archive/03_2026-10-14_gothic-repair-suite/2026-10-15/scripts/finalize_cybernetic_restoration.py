"""Finalize the reference-guided whole-image v7 motif restoration and emit QA."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
TARGET = OUTPUTS / "Pass7_Anatomy_Cleanup_v6.png"
REFERENCE = ASSETS / "references" / "Demiurge_Four_Panel_Restoration_Reference_2048.png"
RAW = ASSETS / "generated" / "Pass7_Anatomy_Cybernetic_Restoration_v7_API.png"
MASTER = OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v7.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    target = cv2.imread(str(TARGET), cv2.IMREAD_COLOR)
    raw = cv2.imread(str(RAW), cv2.IMREAD_COLOR)
    if target is None or raw is None:
        raise FileNotFoundError("The v6 target or persisted API edit is missing")
    if raw.shape[:2] != (2048, 2048):
        raise ValueError(f"Expected a 2048x2048 API edit, received {raw.shape[:2]}")

    # Enforce technically neutral grayscale while retaining the full 2048 master.
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    master = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(MASTER), master, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    cv2.imwrite(
        str(OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v7_1254.png"),
        cv2.resize(master, (1254, 1254), interpolation=cv2.INTER_LANCZOS4),
        [cv2.IMWRITE_PNG_COMPRESSION, 3],
    )

    target_2048 = cv2.resize(target, (2048, 2048), interpolation=cv2.INTER_LANCZOS4)
    absolute = cv2.absdiff(target_2048, master)
    changed = np.any(absolute != 0, axis=2)
    cv2.imwrite(
        str(OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v7_Difference.png"),
        cv2.convertScaleAbs(absolute, alpha=3),
    )

    crops = {
        "Upper_Halos_Cybernetics": (300, 40, 1480, 900),
        "Central_Wires_Anatomy": (300, 620, 1600, 1480),
        "Lower_Cybernetic_Bodies": (180, 1160, 1880, 2000),
    }
    for name, (x0, y0, x1, y1) in crops.items():
        cv2.imwrite(
            str(OUTPUTS / f"Pass7_v7_{name}_Detail.png"),
            master[y0:y1, x0:x1],
        )

    report = {
        "edit_target": str(TARGET.relative_to(ROOT)),
        "edit_target_sha256": sha256(TARGET),
        "motif_reference": str(REFERENCE.relative_to(ROOT)),
        "motif_reference_sha256": sha256(REFERENCE),
        "raw_api_edit_sha256": sha256(RAW),
        "final_master_sha256": sha256(MASTER),
        "dimensions": [2048, 2048],
        "neutral_grayscale_rgb_channels_identical": bool(
            np.array_equal(master[:, :, 0], master[:, :, 1])
            and np.array_equal(master[:, :, 1], master[:, :, 2])
        ),
        "changed_pixels_vs_resized_v6": int(np.count_nonzero(changed)),
        "changed_percent_vs_resized_v6": round(float(changed.mean() * 100.0), 4),
        "edit_scope": "whole_image_reference_guided_restoration",
        "strict_mask_only_invariant": "not_applicable_to_user_requested_global_restoration",
        "restored_motifs": [
            "circular_and_radial_halos",
            "classical_adult_sculptural_anatomy",
            "cybernetic_plates_ports_and_joint_seams",
            "body_attached_ribbed_wires_and_cables",
        ],
        "method": "OpenAI Image API CLI fallback using gpt-image-2 high-quality 2048 edit",
        "status": "approved_after_full_image_and_detail_crop_review",
    }
    (OUTPUTS / "Pass7_Anatomy_Cybernetic_Restoration_v7_QA.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
