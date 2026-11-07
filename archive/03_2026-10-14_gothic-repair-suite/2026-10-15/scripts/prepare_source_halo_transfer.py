"""Prepare the v6-only mask for transferring halo designs from the 2048 source."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v6.png"
MASK = ROOT / "assets" / "Pass7_v6_Source_Halos_Edit_Mask.png"
SELECTION = ROOT / "assets" / "Pass7_v6_Source_Halos_Selection.png"
PREVIEW = ROOT / "outputs" / "Pass7_v6_Source_Halos_Mask_Preview.png"


def annulus(shape: tuple[int, int], center: tuple[int, int], inner: int, outer: int) -> np.ndarray:
    yy, xx = np.ogrid[: shape[0], : shape[1]]
    radius_sq = (xx - center[0]) ** 2 + (yy - center[1]) ** 2
    return ((radius_sq >= inner**2) & (radius_sq <= outer**2)).astype(np.uint8) * 255


def main() -> None:
    destination = cv2.imread(str(DESTINATION), cv2.IMREAD_COLOR)
    if destination is None:
        raise FileNotFoundError(DESTINATION)
    if destination.shape != (1254, 1254, 3):
        raise ValueError(f"Expected 1254x1254 destination, found {destination.shape}")

    # Rear figure: circular ring halo. Front figure: source-style radiating crown halo.
    selection = np.maximum(
        annulus(destination.shape[:2], (529, 130), 34, 86),
        annulus(destination.shape[:2], (459, 207), 30, 91),
    )

    # Preserve the foreground heads, hair, faces, necks, and shoulders exactly.
    cv2.ellipse(selection, (548, 151), (39, 58), -13, 0, 360, 0, -1, cv2.LINE_AA)
    cv2.ellipse(selection, (476, 218), (38, 55), -18, 0, 360, 0, -1, cv2.LINE_AA)
    cv2.fillPoly(
        selection,
        [np.array([(512, 166), (590, 170), (625, 302), (478, 302)], dtype=np.int32)],
        0,
        cv2.LINE_AA,
    )
    cv2.fillPoly(
        selection,
        [np.array([(446, 224), (522, 204), (584, 362), (392, 362)], dtype=np.int32)],
        0,
        cv2.LINE_AA,
    )

    rgba = np.full((1254, 1254, 4), 255, dtype=np.uint8)
    rgba[:, :, 3] = 255 - selection
    Image.fromarray(rgba, "RGBA").save(MASK)
    cv2.imwrite(str(SELECTION), selection)

    preview = destination.copy()
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
