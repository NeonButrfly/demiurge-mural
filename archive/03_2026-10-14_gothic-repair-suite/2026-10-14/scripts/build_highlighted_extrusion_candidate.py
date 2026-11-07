"""Build the two-region candidate from persisted generated replacement textures."""
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import strict_alpha_composite


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v4.png"
WORK = ROOT / "work" / "highlighted_extrusions"

REGIONS = {
    "robe_extrusion": {
        "bounds": (419, 318, 618, 529),
        "mask": "Pass7_RobeExtrusion_Mask.png",
        "replacement": "Robe_Extrusion_Replacement.png",
    },
    "upper_extrusion": {
        "bounds": (619, 252, 810, 444),
        "mask": "Pass7_UpperExtrusion_Mask.png",
        "replacement": "Upper_Extrusion_Replacement.png",
    },
}


def match_luminance(source: np.ndarray, target: np.ndarray, active: np.ndarray) -> np.ndarray:
    src = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dst = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    src_values, dst_values = src[active], dst[active]
    scale = float(dst_values.std() / max(src_values.std(), 1.0))
    adjusted = (src - float(src_values.mean())) * scale + float(dst_values.mean())
    adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def main() -> None:
    working = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if working is None:
        raise FileNotFoundError(BASE)
    for name, config in REGIONS.items():
        mask = cv2.imread(str(ASSETS / config["mask"]), cv2.IMREAD_GRAYSCALE)
        generated = cv2.imread(
            str(ASSETS / "generated" / config["replacement"]), cv2.IMREAD_COLOR
        )
        if mask is None or generated is None:
            raise FileNotFoundError(f"Missing mask or generated replacement for {name}")
        x0, y0, x1, y1 = config["bounds"]
        target = working[y0:y1, x0:x1]
        local_mask = mask[y0:y1, x0:x1]
        generated = cv2.resize(
            generated, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LANCZOS4
        )
        generated = match_luminance(generated, target, local_mask > 0)
        candidate_full = working.copy()
        candidate_full[y0:y1, x0:x1] = generated
        working = strict_alpha_composite(working, candidate_full, mask)
        crop = working[y0:y1, x0:x1]
        cv2.imwrite(str(WORK / f"{name}_candidate.png"), crop)
        cv2.imwrite(
            str(WORK / f"{name}_candidate_4x.png"),
            cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
        )
    cv2.imwrite(str(WORK / "highlighted_extrusions_final_candidate.png"), working)
    print(WORK / "highlighted_extrusions_final_candidate.png")


if __name__ == "__main__":
    main()
