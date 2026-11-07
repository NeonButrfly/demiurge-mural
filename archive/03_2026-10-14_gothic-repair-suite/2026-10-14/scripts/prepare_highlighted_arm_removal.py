"""Extract the user's red unwanted-arm markup into a constrained repair mask."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
REFERENCE = ASSETS / "references" / "Pass7_Highlighted_Unwanted_Arm_User.png"
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v5.png"
WORK = ROOT / "work" / "highlighted_arm_removal"
MASK_PATH = ASSETS / "Pass7_Highlighted_Unwanted_Arm_Mask.png"


def main() -> None:
    marked = cv2.imread(str(REFERENCE), cv2.IMREAD_COLOR)
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if marked is None or base is None:
        raise FileNotFoundError("Annotated arm reference or v5 base is missing")
    if marked.shape != base.shape:
        raise ValueError(f"Reference/base mismatch: {marked.shape} != {base.shape}")

    blue, green, red = cv2.split(marked)
    raw = np.where(
        (red.astype(np.int16) > green.astype(np.int16) + 45)
        & (red.astype(np.int16) > blue.astype(np.int16) + 45)
        & (red > 120),
        255,
        0,
    ).astype(np.uint8)
    raw = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(raw, 8)
    valid = [(label, stats[label]) for label in range(1, count) if stats[label, 4] > 400]
    if len(valid) != 1:
        raise AssertionError(f"Expected one red arm component, found {len(valid)}")
    label, (x, y, width, height, red_area) = valid[0]
    points = np.column_stack(np.where(labels == label)[::-1]).astype(np.int32)
    hard = np.zeros(base.shape[:2], np.uint8)
    cv2.fillConvexPoly(hard, cv2.convexHull(points), 255)
    hard = cv2.dilate(hard, np.ones((5, 5), np.uint8), iterations=1)
    soft = cv2.GaussianBlur(hard, (17, 17), 4.0)
    soft[hard == 0] = 0
    cv2.imwrite(str(MASK_PATH), soft)

    pad = 85
    x0, y0 = max(0, int(x) - pad), max(0, int(y) - pad)
    x1 = min(base.shape[1], int(x + width) + pad)
    y1 = min(base.shape[0], int(y + height) + pad)
    crop = base[y0:y1, x0:x1]
    local_mask = soft[y0:y1, x0:x1]
    overlay = crop.copy()
    overlay[local_mask > 0] = np.asarray([20, 20, 235], dtype=np.uint8)
    WORK.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(WORK / "unwanted_arm_crop.png"), crop)
    cv2.imwrite(str(WORK / "unwanted_arm_mask.png"), local_mask)
    cv2.imwrite(str(WORK / "unwanted_arm_overlay.png"), overlay)
    (WORK / "unwanted_arm_bounds.txt").write_text(
        f"{x0},{y0},{x1},{y1}\n", encoding="utf-8"
    )
    print(
        "red_area", int(red_area), "mask_pixels", int(np.count_nonzero(soft)),
        "crop", (x0, y0, x1, y1)
    )


if __name__ == "__main__":
    main()
