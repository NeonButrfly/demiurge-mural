"""Create reproducible QA evidence from the supplied Pass 7 source and mask."""
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.backends import OpenCVBackend
from gothic_repair.core import RepairProject, match_luminance_and_grain
from gothic_repair.qa import make_qa_bundle


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "assets" / "Gothic_Relief_Pass_7_Original.png"
MASK = ROOT / "assets" / "Pass7_Central_Legs_Inpaint_Mask.png"
OUTPUT = ROOT / "outputs" / "tested_pass7"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    project = RepairProject.from_file(SOURCE)
    mask = cv2.imread(str(MASK), cv2.IMREAD_GRAYSCALE)
    project.set_mask(mask)

    candidate = OpenCVBackend().inpaint(project.working, mask, radius=3)
    candidate = match_luminance_and_grain(candidate, project.working, mask)
    cv2.imwrite(str(OUTPUT / "Pass7_OpenCV_Candidate_UNAPPROVED.png"), candidate)
    cv2.imwrite(str(OUTPUT / "Pass7_OpenCV_Candidate_Difference.png"),
                cv2.convertScaleAbs(cv2.absdiff(project.original, candidate), alpha=4))

    ys, xs = np.where(mask > 0)
    pad = 180
    x0, x1 = max(0, int(xs.min()) - pad), min(project.working.shape[1], int(xs.max()) + pad)
    y0, y1 = max(0, int(ys.min()) - pad), min(project.working.shape[0], int(ys.max()) + pad)
    cv2.imwrite(str(OUTPUT / "Pass7_Central_Legs_Context.png"), project.working[y0:y1, x0:x1])
    cv2.imwrite(str(OUTPUT / "Pass7_Central_Legs_Candidate_Context_UNAPPROVED.png"), candidate[y0:y1, x0:x1])

    # QA export deliberately uses the untouched working state. No anatomy candidate
    # is silently approved, and the invariant report must therefore remain clean.
    make_qa_bundle(project, OUTPUT / "qa_untouched_baseline", 2048)
    print(f"Wrote tested output to {OUTPUT}")


if __name__ == "__main__":
    main()
