"""Extract the user's red markup into two exact repair masks and context crops."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
REFERENCE = ASSETS / "references" / "Pass7_Highlighted_Extrusions_User.png"
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v4.png"
WORK = ROOT / "work" / "highlighted_extrusions"


def constrained_feather(hard: np.ndarray) -> np.ndarray:
    soft = cv2.GaussianBlur(hard, (15, 15), 3.5)
    soft[hard == 0] = 0
    return soft


def main() -> None:
    marked = cv2.imread(str(REFERENCE), cv2.IMREAD_COLOR)
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if marked is None or base is None:
        raise FileNotFoundError("The annotated reference or cumulative v4 base is missing")
    if marked.shape != base.shape:
        raise ValueError(f"Reference/base mismatch: {marked.shape} != {base.shape}")

    blue, green, red = cv2.split(marked)
    raw = np.where(
        (red.astype(np.int16) > green.astype(np.int16) + 55)
        & (red.astype(np.int16) > blue.astype(np.int16) + 55)
        & (red > 135),
        255,
        0,
    ).astype(np.uint8)
    raw = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(raw, 8)
    components: list[tuple[int, int, int, int, int, np.ndarray]] = []
    for label in range(1, count):
        x, y, width, height, area = stats[label]
        if area < 200:
            continue
        component = np.where(labels == label, 255, 0).astype(np.uint8)
        hull_points = np.column_stack(np.where(component > 0)[::-1])
        hull = cv2.convexHull(hull_points.astype(np.int32))
        hard = np.zeros_like(component)
        cv2.fillConvexPoly(hard, hull, 255)
        hard = cv2.dilate(hard, np.ones((5, 5), np.uint8), iterations=1)
        components.append((x, y, width, height, area, hard))
    components.sort(key=lambda item: item[0])
    if len(components) != 2:
        raise AssertionError(f"Expected exactly two red marked regions, found {len(components)}")

    WORK.mkdir(parents=True, exist_ok=True)
    union = np.zeros(base.shape[:2], np.uint8)
    names = ["robe_extrusion", "upper_extrusion"]
    for name, (x, y, width, height, area, hard) in zip(names, components):
        soft = constrained_feather(hard)
        union = cv2.bitwise_or(union, soft)
        cv2.imwrite(str(ASSETS / f"Pass7_{name.title().replace('_', '')}_Mask.png"), soft)
        pad = 70
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(base.shape[1], x + width + pad), min(base.shape[0], y + height + pad)
        crop = base[y0:y1, x0:x1]
        local_mask = soft[y0:y1, x0:x1]
        overlay = crop.copy()
        overlay[local_mask > 0] = np.asarray([20, 20, 235], dtype=np.uint8)
        cv2.imwrite(str(WORK / f"{name}_crop.png"), crop)
        cv2.imwrite(str(WORK / f"{name}_mask.png"), local_mask)
        cv2.imwrite(str(WORK / f"{name}_overlay.png"), overlay)
        (WORK / f"{name}_bounds.txt").write_text(
            f"{x0},{y0},{x1},{y1}\n", encoding="utf-8"
        )
        print(name, "red_area", int(area), "mask_pixels", int(np.count_nonzero(soft)), "crop", (x0, y0, x1, y1))
    cv2.imwrite(str(ASSETS / "Pass7_Highlighted_Extrusions_Mask.png"), union)


if __name__ == "__main__":
    main()
