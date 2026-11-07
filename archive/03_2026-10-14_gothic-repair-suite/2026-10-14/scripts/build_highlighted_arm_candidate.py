"""Build the highlighted unwanted-arm removal candidate from persisted texture."""
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import strict_alpha_composite


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v5.png"
WORK = ROOT / "work" / "highlighted_arm_removal"
BOUNDS = (437, 205, 711, 470)


def match_luminance(source: np.ndarray, target: np.ndarray, active: np.ndarray) -> np.ndarray:
    src = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dst = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    src_values, dst_values = src[active], dst[active]
    scale = float(dst_values.std() / max(src_values.std(), 1.0))
    adjusted = (src - float(src_values.mean())) * scale + float(dst_values.mean())
    adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    mask = cv2.imread(
        str(ASSETS / "Pass7_Highlighted_Unwanted_Arm_Mask.png"), cv2.IMREAD_GRAYSCALE
    )
    generated = cv2.imread(
        str(ASSETS / "generated" / "Highlighted_Unwanted_Arm_Replacement.png"),
        cv2.IMREAD_COLOR,
    )
    if base is None or mask is None or generated is None:
        raise FileNotFoundError("The v5 base, mask, or persisted generated texture is missing")
    x0, y0, x1, y1 = BOUNDS
    target = base[y0:y1, x0:x1]
    local_mask = mask[y0:y1, x0:x1]
    generated = cv2.resize(
        generated, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LANCZOS4
    )
    generated = match_luminance(generated, target, local_mask > 0)
    full = base.copy()
    full[y0:y1, x0:x1] = generated
    candidate = strict_alpha_composite(base, full, mask)
    WORK.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(WORK / "highlighted_arm_final_candidate.png"), candidate)
    crop = candidate[y0:y1, x0:x1]
    cv2.imwrite(str(WORK / "highlighted_arm_candidate_crop.png"), crop)
    cv2.imwrite(
        str(WORK / "highlighted_arm_candidate_crop_4x.png"),
        cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
    )
    print(WORK / "highlighted_arm_final_candidate.png")


if __name__ == "__main__":
    main()
