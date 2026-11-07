"""Prepare a tightly scoped edit mask for restoring the two original Pass 7 halos."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "outputs" / "Pass7_Anatomy_Cybernetic_Restoration_v7.png"
MASK = ROOT / "assets" / "Pass7_Original_Halos_Edit_Mask.png"
SELECTION = ROOT / "assets" / "Pass7_Original_Halos_Selection.png"
PREVIEW = ROOT / "outputs" / "Pass7_Original_Halos_Mask_Preview.png"


def annulus(shape: tuple[int, int], center: tuple[int, int], inner: int, outer: int) -> np.ndarray:
    yy, xx = np.ogrid[: shape[0], : shape[1]]
    distance_sq = (xx - center[0]) ** 2 + (yy - center[1]) ** 2
    return ((distance_sq >= inner**2) & (distance_sq <= outer**2)).astype(np.uint8) * 255


def main() -> None:
    target = cv2.imread(str(TARGET), cv2.IMREAD_COLOR)
    if target is None:
        raise FileNotFoundError(TARGET)
    height, width = target.shape[:2]
    if (width, height) != (2048, 2048):
        raise ValueError(f"Expected 2048x2048 target, found {width}x{height}")

    selection = np.maximum(
        annulus((height, width), (868, 238), 58, 145),
        annulus((height, width), (750, 328), 45, 114),
    )

    # Protect the foreground faces, hair, and necks that occlude the halo rings.
    cv2.ellipse(selection, (895, 245), (62, 94), -12, 0, 360, 0, -1, cv2.LINE_AA)
    cv2.ellipse(selection, (775, 337), (51, 75), -18, 0, 360, 0, -1, cv2.LINE_AA)

    # OpenAI edit masks use transparent pixels for editable regions.
    rgba = np.full((height, width, 4), 255, dtype=np.uint8)
    rgba[:, :, 3] = 255 - selection
    Image.fromarray(rgba, "RGBA").save(MASK)
    cv2.imwrite(str(SELECTION), selection)

    preview = target.copy()
    red = np.zeros_like(preview)
    red[:, :, 2] = 255
    alpha = (selection.astype(np.float32) / 255.0 * 0.62)[:, :, None]
    preview = np.clip(preview * (1.0 - alpha) + red * alpha, 0, 255).astype(np.uint8)
    cv2.imwrite(str(PREVIEW), preview)

    print(MASK)
    print(SELECTION)
    print(PREVIEW)


if __name__ == "__main__":
    main()
