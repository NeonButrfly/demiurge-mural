"""Build local OpenCV removal candidates for the center anatomy defects."""
from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import strict_alpha_composite


ROOT = Path(__file__).parents[1]
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v3.png"
ASSETS = ROOT / "assets"
WORK = ROOT / "work" / "center_cleanup"


def match_luminance(source: np.ndarray, target: np.ndarray, active: np.ndarray) -> np.ndarray:
    src = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dst = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    src_values, dst_values = src[active], dst[active]
    scale = float(dst_values.std() / max(src_values.std(), 1.0))
    adjusted = (src - float(src_values.mean())) * scale + float(dst_values.mean())
    adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def main() -> None:
    image = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    arm = cv2.imread(str(ASSETS / "Pass7_Ownerless_Center_Arm_Mask.png"), cv2.IMREAD_GRAYSCALE)
    bulbs = cv2.imread(str(ASSETS / "Pass7_Central_Bulbous_Forms_Mask.png"), cv2.IMREAD_GRAYSCALE)
    if image is None or arm is None or bulbs is None:
        raise FileNotFoundError("Run prepare_center_cleanup.py first")
    union = cv2.bitwise_or(arm, bulbs)
    hard = np.where(union > 0, 255, 0).astype(np.uint8)

    for name, method in [("telea", cv2.INPAINT_TELEA), ("ns", cv2.INPAINT_NS)]:
        generated = cv2.inpaint(image, hard, 7.0, method)
        candidate = strict_alpha_composite(image, generated, union)
        full_path = WORK / f"center_cleanup_{name}.png"
        cv2.imwrite(str(full_path), candidate)
        x0, y0, x1, y1 = 500, 560, 790, 930
        crop = candidate[y0:y1, x0:x1]
        cv2.imwrite(str(WORK / f"center_cleanup_{name}_crop.png"), crop)
        cv2.imwrite(
            str(WORK / f"center_cleanup_{name}_crop_3x.png"),
            cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
        )
        print(full_path)

    donor = image[405:555, 590:740]
    cv2.imwrite(str(WORK / "center_drapery_donor.png"), donor)
    x0, y0, x1, y1 = 555, 580, 710, 855
    target = image[y0:y1, x0:x1]
    local_mask = union[y0:y1, x0:x1]
    fitted = cv2.resize(donor, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LANCZOS4)
    fitted = match_luminance(fitted, target, local_mask > 0)
    donor_full = image.copy()
    donor_full[y0:y1, x0:x1] = fitted
    donor_candidate = strict_alpha_composite(image, donor_full, union)
    cv2.imwrite(str(WORK / "center_cleanup_donor.png"), donor_candidate)
    crop = donor_candidate[560:930, 500:790]
    cv2.imwrite(str(WORK / "center_cleanup_donor_crop.png"), crop)
    cv2.imwrite(
        str(WORK / "center_cleanup_donor_crop_3x.png"),
        cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
    )
    print(WORK / "center_cleanup_donor.png")

    generated = cv2.imread(
        str(ASSETS / "generated" / "Ownerless_Center_Arm_Texture.png"), cv2.IMREAD_COLOR
    )
    if generated is not None:
        x0, y0, x1, y1 = 500, 560, 790, 930
        generated = cv2.resize(generated, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LANCZOS4)
        generated_full = image.copy()
        generated_full[y0:y1, x0:x1] = generated
        generated_candidate = strict_alpha_composite(image, generated_full, union)
        cv2.imwrite(str(WORK / "center_cleanup_generated.png"), generated_candidate)
        crop = generated_candidate[y0:y1, x0:x1]
        cv2.imwrite(str(WORK / "center_cleanup_generated_crop.png"), crop)
        cv2.imwrite(
            str(WORK / "center_cleanup_generated_crop_3x.png"),
            cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
        )
        print(WORK / "center_cleanup_generated.png")

        arm_candidate = strict_alpha_composite(image, generated_full, arm)
        bulb_hard = np.where(bulbs > 0, 255, 0).astype(np.uint8)
        bulb_fill = cv2.inpaint(arm_candidate, bulb_hard, 3.0, cv2.INPAINT_TELEA)
        hybrid = strict_alpha_composite(arm_candidate, bulb_fill, bulbs)
        cv2.imwrite(str(WORK / "center_cleanup_hybrid.png"), hybrid)
        crop = hybrid[y0:y1, x0:x1]
        cv2.imwrite(str(WORK / "center_cleanup_hybrid_crop.png"), crop)
        cv2.imwrite(
            str(WORK / "center_cleanup_hybrid_crop_3x.png"),
            cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
        )
        print(WORK / "center_cleanup_hybrid.png")

        bulb_generated = cv2.imread(
            str(ASSETS / "generated" / "Central_Bulbous_Forms_Texture.png"),
            cv2.IMREAD_COLOR,
        )
        if bulb_generated is not None:
            bx0, by0, bx1, by1 = 560, 560, 760, 780
            bulb_generated = cv2.resize(
                bulb_generated,
                (bx1 - bx0, by1 - by0),
                interpolation=cv2.INTER_LANCZOS4,
            )
            bulb_full = arm_candidate.copy()
            bulb_full[by0:by1, bx0:bx1] = bulb_generated
            generated_pair = strict_alpha_composite(arm_candidate, bulb_full, bulbs)
            cv2.imwrite(str(WORK / "center_cleanup_generated_pair.png"), generated_pair)
            crop = generated_pair[y0:y1, x0:x1]
            cv2.imwrite(str(WORK / "center_cleanup_generated_pair_crop.png"), crop)
            cv2.imwrite(
                str(WORK / "center_cleanup_generated_pair_crop_3x.png"),
                cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
            )
            print(WORK / "center_cleanup_generated_pair.png")

            seam_hard = np.zeros(image.shape[:2], np.uint8)
            seam_polygon = np.asarray(
                [(566, 654), (594, 646), (621, 668), (626, 712),
                 (612, 748), (584, 752), (563, 722)],
                dtype=np.int32,
            )
            cv2.fillPoly(seam_hard, [seam_polygon], 255)
            seam_hard = cv2.bitwise_and(seam_hard, np.where(arm > 0, 255, 0).astype(np.uint8))
            seam = cv2.GaussianBlur(seam_hard, (17, 17), 4.0)
            seam[seam_hard == 0] = 0
            sx0, sy0, sx1, sy1 = 560, 640, 635, 760
            feather_source = bulb_generated[:120, :90]
            feather_fit = cv2.resize(
                feather_source, (sx1 - sx0, sy1 - sy0), interpolation=cv2.INTER_LANCZOS4
            )
            feather_fit = match_luminance(
                feather_fit,
                generated_pair[sy0:sy1, sx0:sx1],
                seam[sy0:sy1, sx0:sx1] > 0,
            )
            seam_full = generated_pair.copy()
            seam_full[sy0:sy1, sx0:sx1] = feather_fit
            final_candidate = strict_alpha_composite(generated_pair, seam_full, seam)
            cv2.imwrite(str(WORK / "center_cleanup_final_candidate.png"), final_candidate)
            crop = final_candidate[y0:y1, x0:x1]
            cv2.imwrite(str(WORK / "center_cleanup_final_candidate_crop.png"), crop)
            cv2.imwrite(
                str(WORK / "center_cleanup_final_candidate_crop_3x.png"),
                cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
            )
            cv2.imwrite(str(WORK / "center_cleanup_seam_fix_mask.png"), seam)
            print(WORK / "center_cleanup_final_candidate.png")


if __name__ == "__main__":
    main()
