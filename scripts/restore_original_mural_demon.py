"""Remove the void-chested demon insertion and restore the mural's original relief.

Only the previous demon mask is replaced. The adjacent three-woman seam blend
is then reapplied where the masks overlap. Run from the repository root.
"""

from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "outputs" / "mural_character_redesign"


def taper(x: int, start: int, end: int, width: int) -> float:
    return float(np.clip((x - start) / width, 0, 1) * np.clip((end - x) / width, 0, 1))


def main() -> None:
    current = np.asarray(Image.open(WORK / "demiurge_bridge_mericanai_woman.png").convert("RGB"), dtype=np.float64)
    original = np.asarray(Image.open(WORK / "stage_cyan.png").convert("RGB"), dtype=np.float64)
    mask = np.asarray(Image.open(WORK / "magenta_composite_mask.png").convert("L")) > 0
    current[690:1390, 1300:1760][mask] = original[690:1390, 1300:1760][mask]

    background_crop = np.asarray(Image.open(WORK / "original_background_trio_area.png").convert("RGB"), dtype=np.float64)
    background = current.copy()
    background[1120:1740, 1130:1780] = background_crop
    result = current.copy()

    for x in range(1195, 1555):
        local = x - 1195
        center = 1221 + 5 * np.sin(local / 31) + 2 * np.sin(local / 13)
        rows = np.arange(1195, 1250)
        t = np.clip((rows - (center - 16)) / 32, 0, 1)
        t = t * t * (3 - 2 * t)
        weight = (1 - t) * taper(x, 1195, 1555, 32)
        result[1195:1250, x] = current[1195:1250, x] * (1 - weight[:, None]) + background[1195:1250, x] * weight[:, None]

    for x in range(1130, 1650):
        local = x - 1130
        center = 1672 + 5 * np.sin(local / 36) + 3 * np.sin(local / 13)
        rows = np.arange(1650, 1690)
        t = np.clip((rows - (center - 13)) / 26, 0, 1)
        t = t * t * (3 - 2 * t)
        weight = t * taper(x, 1130, 1650, 26)
        result[1650:1690, x] = result[1650:1690, x] * (1 - weight[:, None]) + background[1650:1690, x] * weight[:, None]

    output = WORK / "demiurge_bridge_mericanai_original_demon.png"
    Image.fromarray(np.uint8(np.clip(result, 0, 255))).save(output)
    print(output)


if __name__ == "__main__":
    main()
