"""Prepare review crops for confirmed center-arm and bulbous-form defects."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v3.png"
WORK = ROOT / "work" / "center_cleanup"
ASSETS = ROOT / "assets"

REVIEW_CROPS = {
    "ownerless_center_arm": (500, 560, 790, 930),
    "central_bulbous_forms": (300, 470, 760, 800),
    "lower_center_mix": (430, 680, 790, 1010),
}

MASK_FILES = {
    "ownerless_center_arm": "Pass7_Ownerless_Center_Arm_Mask.png",
    "central_bulbous_forms": "Pass7_Central_Bulbous_Forms_Mask.png",
}


def constrained_feather(hard: np.ndarray, sigma: float = 4.0) -> np.ndarray:
    soft = cv2.GaussianBlur(hard, (19, 19), sigma)
    soft[hard == 0] = 0
    return soft


def build_masks(shape: tuple[int, int]) -> dict[str, np.ndarray]:
    arm = np.zeros(shape, np.uint8)
    arm_path = np.asarray(
        [(590, 638), (602, 680), (612, 724), (628, 770), (642, 822)],
        dtype=np.int32,
    )
    cv2.polylines(arm, [arm_path], False, 255, 40, cv2.LINE_AA)
    cv2.ellipse(arm, (589, 635), (23, 28), -18, 0, 360, 255, -1, cv2.LINE_AA)

    bulbs = np.zeros(shape, np.uint8)
    for center, radius in [
        ((635, 603), 19), ((653, 626), 20), ((626, 657), 18),
        ((654, 682), 19), ((612, 698), 17), ((681, 716), 17),
    ]:
        cv2.circle(bulbs, center, radius, 255, -1, cv2.LINE_AA)
    # Keep a clearance around the skull face and the valid crossed hand.
    cv2.ellipse(bulbs, (690, 625), (34, 40), 0, 0, 360, 0, -1)
    cv2.ellipse(bulbs, (717, 675), (34, 48), 0, 0, 360, 0, -1)
    return {
        "ownerless_center_arm": constrained_feather(arm),
        "central_bulbous_forms": constrained_feather(bulbs),
    }


def main() -> None:
    image = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(BASE)
    WORK.mkdir(parents=True, exist_ok=True)
    masks = build_masks(image.shape[:2])
    for name, mask in masks.items():
        cv2.imwrite(str(ASSETS / MASK_FILES[name]), mask)
        x0, y0, x1, y1 = REVIEW_CROPS[name]
        crop = image[y0:y1, x0:x1]
        local_mask = mask[y0:y1, x0:x1]
        overlay = crop.copy()
        overlay[local_mask > 0] = np.asarray([20, 20, 235], dtype=np.uint8)
        cv2.imwrite(str(WORK / f"{name}_mask.png"), local_mask)
        cv2.imwrite(str(WORK / f"{name}_overlay.png"), overlay)
        print(name, "selected", int(np.count_nonzero(mask)))
    x0, y0, x1, y1 = REVIEW_CROPS["ownerless_center_arm"]
    safe = image[y0:y1, x0:x1].copy()
    # Obscure unrelated exposed figure areas in the service reference. These
    # pixels are never composited; the reference is solely for generating
    # non-anatomical drapery/negative-space texture inside the red mask.
    cv2.rectangle(safe, (0, 115), (105, 305), (36, 36, 36), -1)
    cv2.rectangle(safe, (150, 55), (285, 250), (36, 36, 36), -1)
    cv2.rectangle(safe, (205, 235), (289, 369), (36, 36, 36), -1)
    local_arm = masks["ownerless_center_arm"][y0:y1, x0:x1]
    safe[local_arm > 0] = np.asarray([20, 20, 235], dtype=np.uint8)
    cv2.imwrite(str(WORK / "ownerless_center_arm_safe_reference.png"), safe)

    bx0, by0, bx1, by1 = 560, 560, 760, 780
    bulb_safe = image[by0:by1, bx0:bx1].copy()
    cv2.rectangle(bulb_safe, (95, 35), (199, 219), (36, 36, 36), -1)
    cv2.rectangle(bulb_safe, (0, 115), (85, 219), (36, 36, 36), -1)
    local_bulbs = masks["central_bulbous_forms"][by0:by1, bx0:bx1]
    bulb_safe[local_bulbs > 0] = np.asarray([20, 20, 235], dtype=np.uint8)
    cv2.imwrite(str(WORK / "central_bulbous_forms_safe_reference.png"), bulb_safe)
    for name, (x0, y0, x1, y1) in REVIEW_CROPS.items():
        crop = image[y0:y1, x0:x1]
        cv2.imwrite(str(WORK / f"{name}.png"), crop)
        cv2.imwrite(
            str(WORK / f"{name}_3x.png"),
            cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
        )
        print(name, (x0, y0, x1, y1))


if __name__ == "__main__":
    main()
