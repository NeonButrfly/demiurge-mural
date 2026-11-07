"""Extract the two user-painted replacement regions for issue #13."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
WORK = ROOT / "work" / "v11_erased_region_fills"
BASE = ASSETS / "reviews" / "Pass7_v10_User_Erased_Areas.png"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def solidify(component: np.ndarray) -> np.ndarray:
    component = cv2.morphologyEx(component, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    component = cv2.dilate(
        component,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        iterations=1,
    )
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(component)
    cv2.drawContours(filled, contours, -1, 255, cv2.FILLED)
    return filled


def crop(
    image: np.ndarray,
    mask: np.ndarray,
    name: str,
    bounds: tuple[int, int, int, int],
) -> dict[str, int]:
    x0, y0, x1, y1 = bounds
    save(WORK / f"{name}_target.png", image[y0:y1, x0:x1])
    save(WORK / f"{name}_mask.png", mask[y0:y1, x0:x1])
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if base is None:
        raise FileNotFoundError(BASE)
    height, width = base.shape[:2]
    hsv = cv2.cvtColor(base, cv2.COLOR_BGR2HSV)
    yellow = cv2.inRange(hsv, np.array((16, 55, 65), np.uint8), np.array((42, 255, 255), np.uint8))
    yy, xx = np.indices((height, width))
    top = np.where((yellow > 0) & (yy < int(height * 0.25)), 255, 0).astype(np.uint8)
    lower = np.where((yellow > 0) & (yy > int(height * 0.62)), 255, 0).astype(np.uint8)
    top = solidify(top)
    lower = solidify(lower)

    masks = {"demon_upper_body": top, "reclining_replacement": lower}
    bounds = {
        "demon_upper_body": (560, 0, 940, 270),
        "reclining_replacement": (520, 700, width, height),
    }
    union = cv2.bitwise_or(top, lower)
    preview = base.astype(np.float32)
    colors = ((0, 170, 255), (255, 80, 30))
    manifest: dict[str, object] = {
        "issue": 13,
        "base": str(BASE.relative_to(ROOT)),
        "dimensions": [width, height],
        "regions": {},
    }
    for (name, mask), color in zip(masks.items(), colors, strict=True):
        save(ASSETS / f"Pass7_v11_{name}_Mask.png", mask)
        region_bounds = crop(base, mask, name, bounds[name])
        manifest["regions"][name] = {
            "pixels": int(np.count_nonzero(mask)),
            "bounds": region_bounds,
        }
        alpha = (mask.astype(np.float32) / 255.0 * 0.55)[:, :, None]
        preview = preview * (1.0 - alpha) + np.full_like(preview, color, np.float32) * alpha

    save(ASSETS / "Pass7_v11_Erased_Regions_Union_Mask.png", union)
    save(OUTPUTS / "Pass7_v11_Erased_Regions_Mask_Preview.png", np.clip(preview, 0, 255).astype(np.uint8))
    manifest["union_pixels"] = int(np.count_nonzero(union))
    manifest["policy"] = "two replacement masks; all other supplied-image pixels remain byte-identical"
    (ASSETS / "Pass7_v11_Erased_Regions_Manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
