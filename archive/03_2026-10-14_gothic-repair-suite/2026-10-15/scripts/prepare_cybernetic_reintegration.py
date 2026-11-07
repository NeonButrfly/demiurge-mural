"""Prepare explicit masks for the v8 cybernetic reintegration pass."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
BASE = OUTPUTS / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"


def save(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    red = cv2.imread(str(ASSETS / "Pass7_PDF_Red_Replacement_Mask.png"), cv2.IMREAD_GRAYSCALE)
    if base is None or red is None:
        raise FileNotFoundError("v7 destination or PDF red mask is missing")

    count, labels, stats, _ = cv2.connectedComponentsWithStats((red > 0).astype(np.uint8), 8)
    components = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= 500:
            components.append(((labels == label).astype(np.uint8) * 255, tuple(map(int, stats[label]))))
    components.sort(key=lambda item: item[1][1])
    if len(components) != 3:
        raise AssertionError(f"Expected three red regions, found {len(components)}")

    demon = cv2.dilate(components[0][0], np.ones((5, 5), np.uint8), iterations=1)
    reclining = components[2][0]

    hooded = np.zeros(base.shape[:2], np.uint8)
    # Narrow centerline follows the already-valid upper arm below the hooded face.
    cv2.polylines(
        hooded,
        [np.array([[342, 655], [370, 670], [405, 678], [438, 670]], dtype=np.int32)],
        isClosed=False,
        color=255,
        thickness=31,
        lineType=cv2.LINE_AA,
    )
    existing_hand = cv2.imread(
        str(ASSETS / "Pass7_Hooded_Cybernetic_Hand_Mask.png"), cv2.IMREAD_GRAYSCALE
    )
    if existing_hand is None:
        raise FileNotFoundError("Existing hooded hand mask is missing")
    hooded = cv2.bitwise_or(hooded, existing_hand)

    filigree = np.zeros(base.shape[:2], np.uint8)
    ellipses = [
        ((361, 432), (29, 43), -18),
        ((501, 704), (34, 54), -8),
        ((688, 708), (29, 44), 12),
        ((459, 1002), (48, 57), -16),
        ((799, 1065), (51, 63), 8),
    ]
    for center, axes, angle in ellipses:
        cv2.ellipse(filigree, center, axes, angle, 0, 360, 255, -1)

    # Keep motif overlays away from all replacement regions.
    reserved = cv2.bitwise_or(cv2.bitwise_or(demon, reclining), hooded)
    filigree[reserved > 0] = 0
    union = cv2.bitwise_or(reserved, filigree)

    paths = {
        "demon_claw": ASSETS / "Pass7_v8_Demon_Claw_Mask.png",
        "reclining_human": ASSETS / "Pass7_v8_Reclining_Human_Mask.png",
        "hooded_arm": ASSETS / "Pass7_v8_Hooded_Arm_Mask.png",
        "surface_filigree": ASSETS / "Pass7_v8_Surface_Filigree_Mask.png",
        "union": ASSETS / "Pass7_v8_Cybernetic_Reintegration_Union_Mask.png",
    }
    for key, image in (
        ("demon_claw", demon),
        ("reclining_human", reclining),
        ("hooded_arm", hooded),
        ("surface_filigree", filigree),
        ("union", union),
    ):
        save(paths[key], image)

    preview = base.copy().astype(np.float32)
    colors = [
        (demon, (0, 0, 255)),
        (reclining, (255, 80, 180)),
        (hooded, (255, 160, 0)),
        (filigree, (0, 215, 255)),
    ]
    for mask, color in colors:
        alpha = (mask.astype(np.float32) / 255.0 * 0.55)[:, :, None]
        overlay = np.full_like(preview, color, dtype=np.float32)
        preview = preview * (1.0 - alpha) + overlay * alpha
    preview_path = OUTPUTS / "Pass7_v8_Cybernetic_Reintegration_Mask_Preview.png"
    save(preview_path, np.clip(preview, 0, 255).astype(np.uint8))

    manifest = {
        "issue": 11,
        "destination": str(BASE.relative_to(ROOT)),
        "masks": {key: str(path.relative_to(ROOT)) for key, path in paths.items()},
        "selected_pixels": {
            "demon_claw": int(np.count_nonzero(demon)),
            "reclining_human": int(np.count_nonzero(reclining)),
            "hooded_arm": int(np.count_nonzero(hooded)),
            "surface_filigree": int(np.count_nonzero(filigree)),
            "union": int(np.count_nonzero(union)),
        },
        "anatomy_policy": "reclining silhouette replacement plus surface-only cybernetic overlays; all other anatomy protected",
    }
    (ASSETS / "Pass7_v8_Cybernetic_Reintegration_Manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
