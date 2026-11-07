"""Fill the user's two yellow replacement areas with isolated generated donors."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
GENERATED = ASSETS / "generated"
OUTPUTS = ROOT / "outputs"
BASE = ASSETS / "reviews" / "Pass7_v10_User_Erased_Areas.png"
FINAL = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gray3(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def tone_match(patch: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
    selected = mask > 0
    ring = cv2.dilate(selected.astype(np.uint8), np.ones((19, 19), np.uint8), iterations=1) > 0
    ring &= ~selected
    patch_gray = cv2.cvtColor(gray3(patch), cv2.COLOR_BGR2GRAY).astype(np.float32)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY).astype(np.float32)
    source_values = patch_gray[selected]
    target_values = target_gray[ring] if np.count_nonzero(ring) > 32 else target_gray[selected]
    gain = float(np.clip(np.std(target_values) / max(np.std(source_values), 1.0), 0.78, 1.18))
    matched = (patch_gray - float(np.mean(source_values))) * gain + float(np.mean(target_values))
    matched = np.clip(matched, 0, 255).astype(np.uint8)
    detail = cv2.addWeighted(matched, 1.35, cv2.GaussianBlur(matched, (0, 0), 0.65), -0.35, 0)
    return cv2.cvtColor(detail, cv2.COLOR_GRAY2BGR)


def place_crop(
    canvas: np.ndarray,
    donor: np.ndarray,
    mask: np.ndarray,
    bounds: dict[str, int],
    feather: float,
) -> None:
    x0, y0, x1, y1 = (bounds[key] for key in ("x0", "y0", "x1", "y1"))
    target = canvas[y0:y1, x0:x1]
    local_mask = mask[y0:y1, x0:x1]
    patch = cv2.resize(donor, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    patch = tone_match(patch, target, local_mask)
    distance = cv2.distanceTransform((local_mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    alpha = np.minimum(distance / feather, 1.0)[:, :, None]
    mixed = np.clip(target.astype(np.float32) * (1.0 - alpha) + patch.astype(np.float32) * alpha, 0, 255)
    selected = local_mask > 0
    target[selected] = gray3(mixed.astype(np.uint8))[selected]


def details(image: np.ndarray) -> np.ndarray:
    upper = image[0:285, 520:960]
    lower = image[680:1131, 490:1131]
    upper = cv2.resize(upper, (720, 460), interpolation=cv2.INTER_LANCZOS4)
    lower = cv2.resize(lower, (720, 460), interpolation=cv2.INTER_LANCZOS4)
    return np.vstack((upper, lower))


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    manifest = json.loads((ASSETS / "Pass7_v11_Erased_Regions_Manifest.json").read_text(encoding="utf-8"))
    masks = {
        name: cv2.imread(str(ASSETS / f"Pass7_v11_{name}_Mask.png"), cv2.IMREAD_GRAYSCALE)
        for name in ("demon_upper_body", "reclining_replacement")
    }
    union = cv2.imread(str(ASSETS / "Pass7_v11_Erased_Regions_Union_Mask.png"), cv2.IMREAD_GRAYSCALE)
    donors = {
        "demon_upper_body": cv2.imread(str(GENERATED / "Pass7_v11_Demon_Upper_Body_Donor.png"), cv2.IMREAD_COLOR),
        "reclining_replacement": cv2.imread(str(GENERATED / "Pass7_v11_Reclining_Figure_Donor.png"), cv2.IMREAD_COLOR),
    }
    if base is None or union is None or any(value is None for value in (*masks.values(), *donors.values())):
        raise FileNotFoundError("A v11 base, mask, or donor is missing")

    result = base.copy()
    place_crop(
        result,
        donors["demon_upper_body"],
        masks["demon_upper_body"],
        manifest["regions"]["demon_upper_body"]["bounds"],
        feather=6.0,
    )
    place_crop(
        result,
        donors["reclining_replacement"],
        masks["reclining_replacement"],
        manifest["regions"]["reclining_replacement"]["bounds"],
        feather=9.0,
    )
    save(FINAL, result)

    selected = union > 0
    absolute = cv2.absdiff(base, result)
    changed = np.any(absolute != 0, axis=2)
    violations = changed & ~selected
    difference_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled_Difference.png"
    out_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled_OutOfMask.png"
    details_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled_Details.png"
    save(difference_path, cv2.convertScaleAbs(absolute, alpha=4.0))
    violation_view = np.zeros_like(result)
    violation_view[violations] = (0, 0, 255)
    save(out_path, violation_view)
    save(details_path, details(result))

    report = {
        "issue": 13,
        "base": str(BASE.relative_to(ROOT)),
        "base_sha256": sha256(BASE),
        "final": str(FINAL.relative_to(ROOT)),
        "final_sha256": sha256(FINAL),
        "dimensions": [int(result.shape[1]), int(result.shape[0])],
        "selected_pixels": int(np.count_nonzero(selected)),
        "changed_pixels": int(np.count_nonzero(changed)),
        "changed_pixels_outside_masks": int(np.count_nonzero(violations)),
        "outside_masks_byte_identical": bool(np.count_nonzero(violations) == 0),
        "changed_pixels_neutral_grayscale": bool(
            np.array_equal(result[:, :, 0][changed], result[:, :, 1][changed])
            and np.array_equal(result[:, :, 1][changed], result[:, :, 2][changed])
        ),
        "repairs": {
            "demon_upper_body": "continuous demon head, neck, shoulder, arm, wrist, and five-talon claw",
            "reclining_replacement": "one fully draped reclining figure with connected anatomy",
        },
    }
    qa_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL,
            difference_path,
            out_path,
            details_path,
            qa_path,
            OUTPUTS / "Pass7_v11_Erased_Regions_Mask_Preview.png",
            ASSETS / "Pass7_v11_Erased_Regions_Manifest.json",
            ASSETS / "Pass7_v11_Erased_Regions_Union_Mask.png",
            ASSETS / "Pass7_v11_demon_upper_body_Mask.png",
            ASSETS / "Pass7_v11_reclining_replacement_Mask.png",
            GENERATED / "Pass7_v11_Demon_Upper_Body_Donor.png",
            GENERATED / "Pass7_v11_Reclining_Figure_Donor.png",
            ROOT / "docs" / "prompts" / "v11-erased-region-fill-prompts.md",
        ):
            bundle.write(path, path.relative_to(ROOT))

    if np.count_nonzero(violations):
        raise AssertionError("Pixels changed outside the two user-painted replacement masks")
    if not report["changed_pixels_neutral_grayscale"]:
        raise AssertionError("Changed pixels are not neutral grayscale")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
