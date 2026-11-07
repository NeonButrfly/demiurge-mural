"""Prepare focused review crops and strictly bounded masks for the final anatomy pass."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
BASE = ROOT / "outputs" / "Pass7_Anatomy_Repairs_v2.png"
WORK = ROOT / "work" / "full_anatomy_cleanup"
ASSETS = ROOT / "assets"

# Coordinates are in the 1254 x 1254 Pass 7 image. Each polygon is deliberately
# smaller than its context crop so the generated context can never overwrite it.
REGIONS = {
    "reclining_hip_legs": {
        "mask_file": "Pass7_Reclining_Hip_Legs_Mask.png",
        "crop": (400, 805, 620, 970),
        "polygon": [
            (420, 805), (462, 805), (508, 810), (550, 828),
            (586, 850), (602, 880), (588, 914), (558, 945),
            (516, 958), (474, 944), (440, 910), (418, 864),
        ],
    },
    "lower_center_arm_cluster": {
        "crop": (500, 805, 760, 1065),
        "polygon": [
            (543, 883), (571, 860), (605, 869), (632, 902),
            (661, 935), (686, 960), (674, 1006), (638, 1026),
            (602, 1008), (578, 974), (550, 943),
        ],
    },
}


def make_mask(shape: tuple[int, int], polygon: list[tuple[int, int]]) -> np.ndarray:
    hard = np.zeros(shape, np.uint8)
    cv2.fillPoly(hard, [np.asarray(polygon, dtype=np.int32)], 255)
    soft = cv2.GaussianBlur(hard, (19, 19), 4.5)
    soft[hard == 0] = 0
    return soft


def main() -> None:
    image = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(BASE)
    WORK.mkdir(parents=True, exist_ok=True)
    for name, config in REGIONS.items():
        x0, y0, x1, y1 = config["crop"]
        crop = image[y0:y1, x0:x1]
        mask = make_mask(image.shape[:2], config["polygon"])
        if "mask_file" in config:
            cv2.imwrite(str(ASSETS / config["mask_file"]), mask)
        local_mask = mask[y0:y1, x0:x1]
        overlay = crop.copy()
        active = local_mask > 0
        overlay[active] = np.asarray([20, 20, 235], dtype=np.uint8)
        cv2.imwrite(str(WORK / f"{name}_crop.png"), crop)
        cv2.imwrite(
            str(WORK / f"{name}_crop_4x.png"),
            cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
        )
        cv2.imwrite(str(WORK / f"{name}_mask.png"), local_mask)
        cv2.imwrite(str(WORK / f"{name}_overlay.png"), overlay)
        print(f"{name}: crop={config['crop']} selected={np.count_nonzero(mask)}")


if __name__ == "__main__":
    main()
