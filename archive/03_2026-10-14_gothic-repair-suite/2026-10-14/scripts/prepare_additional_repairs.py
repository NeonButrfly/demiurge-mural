"""Build reproducible local masks and focused crops for Pass 7 issues #3 and #4."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
BASE = ROOT / "outputs" / "Pass7_Central_Legs_Repair.png"
ASSETS = ROOT / "assets"
WORK = ROOT / "work" / "additional_repairs"

REGIONS = {
    "hooded_hand": {
        "crop": (330, 565, 500, 735),
        "polygon": [(405, 650), (420, 635), (450, 632), (480, 646),
                    (496, 665), (490, 690), (462, 710), (430, 700),
                    (410, 680)],
        "mask_file": "Pass7_Hooded_Cybernetic_Hand_Mask.png",
    },
    "spear_grip": {
        "crop": (780, 720, 900, 840),
        "polygon": [(808, 765), (820, 749), (842, 750), (858, 762),
                    (865, 780), (858, 798), (840, 810), (820, 798),
                    (810, 782)],
        "mask_file": "Pass7_Spear_Grip_Mask.png",
    },
}


def make_mask(shape: tuple[int, int], polygon: list[tuple[int, int]]) -> np.ndarray:
    hard = np.zeros(shape, np.uint8)
    cv2.fillPoly(hard, [np.array(polygon, np.int32)], 255)
    # Feather is constrained to the selected polygon: no alpha is introduced outside it.
    soft = cv2.GaussianBlur(hard, (17, 17), 4)
    soft[hard == 0] = 0
    return soft


def main():
    image = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(BASE)
    WORK.mkdir(parents=True, exist_ok=True)
    for name, config in REGIONS.items():
        mask = make_mask(image.shape[:2], config["polygon"])
        mask_path = ASSETS / config["mask_file"]
        cv2.imwrite(str(mask_path), mask)
        x0, y0, x1, y1 = config["crop"]
        cv2.imwrite(str(WORK / f"{name}_crop.png"), image[y0:y1, x0:x1])
        cv2.imwrite(str(WORK / f"{name}_mask.png"), mask[y0:y1, x0:x1])
        overlay = image[y0:y1, x0:x1].copy()
        active = mask[y0:y1, x0:x1] > 0
        overlay[active] = np.clip(overlay[active].astype(np.float32) * .55 + np.array([20, 20, 230]) * .45, 0, 255)
        cv2.imwrite(str(WORK / f"{name}_overlay.png"), overlay)
        print(f"{name}: {np.count_nonzero(mask)} selected pixels; {mask_path}")


if __name__ == "__main__":
    main()
