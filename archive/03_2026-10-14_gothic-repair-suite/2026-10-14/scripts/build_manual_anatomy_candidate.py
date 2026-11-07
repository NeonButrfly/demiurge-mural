"""Build a local donor-patch candidate from already approved Pass 7 anatomy."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).parents[1]
WORK = ROOT / "work" / "full_anatomy_cleanup"
BASE = ROOT / "outputs" / "Pass7_Anatomy_Repairs_v2.png"
DONOR = ROOT / "outputs" / "Pass7_Central_Legs_Repair_Crop.png"


def match_luminance(source: np.ndarray, target: np.ndarray, active: np.ndarray) -> np.ndarray:
    """Match grayscale donor statistics to the destination without adding color."""
    src = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dst = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    src_values = src[active]
    dst_values = dst[active]
    scale = float(dst_values.std() / max(src_values.std(), 1.0))
    adjusted = (src - float(src_values.mean())) * scale + float(dst_values.mean())
    adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    donor = cv2.imread(str(DONOR), cv2.IMREAD_COLOR)
    mask = cv2.imread(str(WORK / "reclining_hip_legs_mask.png"), cv2.IMREAD_GRAYSCALE)
    if base is None or donor is None or mask is None:
        raise FileNotFoundError("Run prepare_full_anatomy_cleanup.py and retain the approved v2 output")

    grid = donor.copy()
    for value in range(0, min(grid.shape[:2]), 20):
        cv2.line(grid, (value, 0), (value, grid.shape[0] - 1), (0, 0, 255), 1)
        cv2.line(grid, (0, value), (grid.shape[1] - 1, value), (0, 0, 255), 1)
        cv2.putText(grid, str(value), (value + 2, 12), cv2.FONT_HERSHEY_PLAIN, 0.7, (0, 0, 255), 1)
        cv2.putText(grid, str(value), (2, value + 12), cv2.FONT_HERSHEY_PLAIN, 0.7, (0, 0, 255), 1)
    cv2.imwrite(str(WORK / "approved_legs_donor_grid.png"), grid)

    x0, y0, x1, y1 = 400, 805, 620, 970
    target = base[y0:y1, x0:x1]
    # The donor contains the approved gown, two separated lower legs, ankles and feet.
    donor_focus = donor[8:238, 18:242]
    donor_fit = cv2.resize(donor_focus, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LANCZOS4)
    donor_fit = match_luminance(donor_fit, target, mask > 0)

    alpha = mask.astype(np.float32) / 255.0
    alpha = alpha[..., None]
    candidate = np.rint(target * (1.0 - alpha) + donor_fit * alpha).clip(0, 255).astype(np.uint8)
    cv2.imwrite(str(WORK / "reclining_hip_legs_manual_candidate.png"), candidate)
    cv2.imwrite(
        str(WORK / "reclining_hip_legs_manual_candidate_4x.png"),
        cv2.resize(candidate, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
    )
    print(WORK / "reclining_hip_legs_manual_candidate.png")


if __name__ == "__main__":
    main()
