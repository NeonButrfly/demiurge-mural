from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .core import RepairProject, out_of_mask_diff


def make_qa_bundle(project: RepairProject, folder: str | Path, export_size: int = 2048) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    approved = project.combined_approved_mask()
    count, violations = out_of_mask_diff(project.original, project.working, approved)
    overlay = project.working.copy()
    tint = np.zeros_like(overlay)
    tint[..., 2] = approved
    overlay = cv2.addWeighted(overlay, 0.72, tint, 0.28, 0)
    diff = cv2.absdiff(project.original, project.working)
    cv2.imwrite(str(folder / "01_before.png"), project.original)
    cv2.imwrite(str(folder / "02_after.png"), project.working)
    cv2.imwrite(str(folder / "03_mask_overlay.png"), overlay)
    cv2.imwrite(str(folder / "04_absolute_difference.png"), diff)
    cv2.imwrite(str(folder / "05_out_of_mask_violations.png"), violations)
    project.export(folder / f"06_final_{export_size}x{export_size}.png", export_size)
    project.export_heightmap(folder / f"07_heightmap_draft_{export_size}x{export_size}.png", export_size)
    report = {
        "source_sha256": project.original_sha256,
        "out_of_mask_changed_pixels": count,
        "strict_invariant_passed": count == 0,
        "export_size": export_size,
        "regions": [{"id": r.id, "name": r.name, "status": r.status,
                     "mask_pixels": int(np.count_nonzero(r.mask))} for r in project.regions],
        "note": "Heightmap is a luminance draft, not validated physical relief geometry.",
    }
    (folder / "QA_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return folder
