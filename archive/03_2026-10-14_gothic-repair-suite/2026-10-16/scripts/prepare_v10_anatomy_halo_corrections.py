"""Prepare five isolated correction regions for issue #13."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
WORK = ROOT / "work" / "v10_anatomy_halo"
BASE = OUTPUTS / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections.png"
REFERENCE = ASSETS / "references" / "Demiurge_Four_Panel_Restoration_Reference_2048.png"
ANNOTATED = ASSETS / "reviews" / "Pass7_v9_User_Review_Anatomy_Halo_Bubbles.png"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def annulus(shape: tuple[int, int], center: tuple[int, int], inner: int, outer: int) -> np.ndarray:
    yy, xx = np.ogrid[: shape[0], : shape[1]]
    d2 = (xx - center[0]) ** 2 + (yy - center[1]) ** 2
    return ((d2 >= inner**2) & (d2 <= outer**2)).astype(np.uint8) * 255


def crop(image: np.ndarray, mask: np.ndarray, name: str, bounds: tuple[int, int, int, int]) -> dict[str, int]:
    x0, y0, x1, y1 = bounds
    save(WORK / f"{name}_target.png", image[y0:y1, x0:x1])
    save(WORK / f"{name}_mask.png", mask[y0:y1, x0:x1])
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    reference = cv2.imread(str(REFERENCE), cv2.IMREAD_COLOR)
    annotated = cv2.imread(str(ANNOTATED), cv2.IMREAD_COLOR)
    if base is None or reference is None or annotated is None:
        raise FileNotFoundError("v9 base, annotated review, or original reference missing")
    if annotated.shape != base.shape:
        raise AssertionError(f"Annotated review shape {annotated.shape} does not match v9 {base.shape}")
    shape = base.shape[:2]

    b, g, r = cv2.split(annotated)
    yy, xx = np.indices(shape)
    yellow = (r > 100) & (g > 78) & (r > b * 1.18) & (g > b * 1.10)
    yellow = cv2.morphologyEx(yellow.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    demon = np.where(yellow.astype(bool) & (xx > 650) & (xx < 930) & (yy < 270), 255, 0).astype(np.uint8)
    reclining = np.where(yellow.astype(bool) & (yy > 790), 255, 0).astype(np.uint8)
    halo_paint = np.where(yellow.astype(bool) & (xx < 620) & (yy < 310), 255, 0).astype(np.uint8)
    bump = np.where(yellow.astype(bool) & (xx < 700) & (yy > 300) & (yy < 760), 255, 0).astype(np.uint8)
    bubbles = np.where(yellow.astype(bool) & (xx > 900) & (yy < 370), 255, 0).astype(np.uint8)
    bubbles = cv2.dilate(bubbles, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)), iterations=1)
    # The translucent review paint sits inside the bulb silhouettes. Include
    # the complete two marked forms so no rounded rim survives compositing.
    cv2.ellipse(bubbles, (966, 49), (43, 42), 0, 0, 360, 255, -1, cv2.LINE_AA)
    cv2.ellipse(bubbles, (1018, 269), (44, 73), 0, 0, 360, 255, -1, cv2.LINE_AA)

    # Cover both the incorrectly placed crown and its corrected centered position while protecting the face.
    halo_geometry = cv2.bitwise_or(annulus(shape, (459, 207), 30, 91), annulus(shape, (478, 216), 31, 91))
    halo = cv2.bitwise_or(halo_paint, halo_geometry)
    cv2.ellipse(halo, (478, 216), (41, 58), -18, 0, 360, 0, -1, cv2.LINE_AA)
    cv2.fillPoly(halo, [np.array([(444, 228), (525, 203), (588, 365), (388, 365)], np.int32)], 0)

    masks = {
        "demon_arm": demon,
        "reclining_lady": reclining,
        "spiked_halo": halo,
        "abdominal_bump": bump,
        "upper_right_bubbles": bubbles,
    }
    bounds = {
        "demon_arm": (650, 0, 1000, 280),
        "reclining_lady": (570, 810, 1210, 1254),
        "spiked_halo": (350, 105, 570, 315),
        "abdominal_bump": (390, 290, 710, 750),
        "upper_right_bubbles": (900, 0, 1090, 370),
    }
    manifest: dict[str, object] = {"issue": 13, "base": str(BASE.relative_to(ROOT)), "regions": {}}
    union = np.zeros(shape, np.uint8)
    preview = base.astype(np.float32)
    colors = [(0, 210, 255), (255, 90, 30), (200, 80, 220), (20, 20, 240), (0, 170, 255)]
    for (name, mask), color in zip(masks.items(), colors, strict=True):
        union = cv2.bitwise_or(union, mask)
        save(ASSETS / f"Pass7_v10_{name}_Mask.png", mask)
        region_bounds = crop(base, mask, name, bounds[name])
        manifest["regions"][name] = {"pixels": int(np.count_nonzero(mask)), "bounds": region_bounds}
        alpha = (mask.astype(np.float32) / 255.0 * 0.58)[:, :, None]
        preview = preview * (1.0 - alpha) + np.full_like(preview, color, np.float32) * alpha

    # Focused original-source references for donor generation.
    save(WORK / "demon_original_reference.png", reference[90:590, 830:1360])
    save(WORK / "reclining_original_reference.png", reference[900:1510, 670:1540])
    # The full abdominal crop contains unrelated exposed figures that can block
    # image editing.  Keep the approved fabric selection plus a narrow seam
    # context and neutralize everything else for a fabric-only donor request.
    x0, y0, x1, y1 = bounds["abdominal_bump"]
    fabric_crop = base[y0:y1, x0:x1]
    fabric_mask = bump[y0:y1, x0:x1]
    context = cv2.dilate((fabric_mask > 0).astype(np.uint8), np.ones((31, 31), np.uint8), iterations=1) > 0
    neutral = cv2.GaussianBlur(fabric_crop, (0, 0), 18.0)
    neutral = cv2.convertScaleAbs(neutral, alpha=0.35, beta=35)
    fabric_only = neutral
    fabric_only[context] = fabric_crop[context]
    save(WORK / "abdominal_bump_fabric_only_target.png", fabric_only)
    save(ASSETS / "Pass7_v10_Anatomy_Halo_Union_Mask.png", union)
    save(OUTPUTS / "Pass7_v10_Anatomy_Halo_Mask_Preview.png", np.clip(preview, 0, 255).astype(np.uint8))
    manifest["union_pixels"] = int(np.count_nonzero(union))
    manifest["policy"] = "five independent masks; all other v9 pixels remain byte-identical"
    (ASSETS / "Pass7_v10_Anatomy_Halo_Manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
