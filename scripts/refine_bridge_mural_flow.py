"""Feather the earlier three-woman insert into the Demiurge mural background.

Only two narrow boundary bands are edited. The source trio and Kharn Sagara
remain untouched. Run from the repository root.
"""

from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "outputs" / "mural_character_redesign"
CURRENT = WORK / "demiurge_redesigned_three_groups.png"
BACKGROUND_CROP = WORK / "original_background_trio_area.png"
OUTPUT = WORK / "demiurge_bridge_flow_refined.png"
CROP_LEFT, CROP_TOP = 1130, 1120


def taper(x: int, start: int, end: int, width: int) -> float:
    return float(np.clip((x - start) / width, 0, 1) * np.clip((end - x) / width, 0, 1))


def main() -> None:
    current = np.asarray(Image.open(CURRENT).convert("RGB"), dtype=np.float64)
    background_crop = np.asarray(Image.open(BACKGROUND_CROP).convert("RGB"), dtype=np.float64)
    background = current.copy()
    h, w = background_crop.shape[:2]
    background[CROP_TOP:CROP_TOP + h, CROP_LEFT:CROP_LEFT + w] = background_crop
    result = current.copy()

    # Above the group, retain the original drapery and fade into the insert.
    x0, x1, y0, y1 = 1195, 1555, 1195, 1250
    for x in range(x0, x1):
        local = x - x0
        center = 1221 + 5 * np.sin(local / 31) + 2 * np.sin(local / 13)
        ys = np.arange(y0, y1)
        t = np.clip((ys - (center - 16)) / 32, 0, 1)
        t = t * t * (3 - 2 * t)
        weight = (1 - t) * taper(x, x0, x1, 32)
        result[y0:y1, x] = current[y0:y1, x] * (1 - weight[:, None]) + background[y0:y1, x] * weight[:, None]

    # Below the group, vary the fade line to avoid a straight rectangular edge.
    x0, x1, y0, y1 = 1130, 1650, 1650, 1690
    for x in range(x0, x1):
        local = x - x0
        center = 1672 + 5 * np.sin(local / 36) + 3 * np.sin(local / 13)
        ys = np.arange(y0, y1)
        t = np.clip((ys - (center - 13)) / 26, 0, 1)
        t = t * t * (3 - 2 * t)
        weight = t * taper(x, x0, x1, 26)
        result[y0:y1, x] = result[y0:y1, x] * (1 - weight[:, None]) + background[y0:y1, x] * weight[:, None]

    Image.fromarray(np.uint8(np.clip(result, 0, 255))).save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
