"""Register the user's scanned PDF annotations to the current 1254px master."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = ROOT / "assets" / "references" / "10152026_Annotated_Page_Upright.jpg"
DESTINATION = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png"
REGISTERED = ROOT / "assets" / "references" / "10152026_Registered_Annotation.png"
YELLOW = ROOT / "assets" / "Pass7_PDF_Yellow_Anatomy_Mask.png"
RED = ROOT / "assets" / "Pass7_PDF_Red_Replacement_Mask.png"
UNION = ROOT / "assets" / "Pass7_PDF_Annotated_Union_Mask.png"
YELLOW_EDIT = ROOT / "assets" / "Pass7_PDF_Yellow_Anatomy_Edit_Mask.png"
RED_EDIT = ROOT / "assets" / "Pass7_PDF_Red_Replacement_Edit_Mask.png"
PREVIEW = ROOT / "outputs" / "Pass7_PDF_Annotations_Registered_Preview.png"
MANIFEST = ROOT / "assets" / "Pass7_PDF_Annotation_Regions.json"


def filtered_components(mask: np.ndarray, minimum_area: int = 20) -> tuple[np.ndarray, list[dict]]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    kept = np.zeros_like(mask)
    regions: list[dict] = []
    for label in range(1, count):
        x, y, width, height, area = [int(value) for value in stats[label]]
        if area < minimum_area:
            continue
        kept[labels == label] = 255
        regions.append({"x": x, "y": y, "width": width, "height": height, "pixels": area})
    regions.sort(key=lambda item: (item["y"], item["x"]))
    return kept, regions


def rgba_edit_mask(selection: np.ndarray, path: Path) -> None:
    rgba = np.full((*selection.shape, 4), 255, dtype=np.uint8)
    rgba[:, :, 3] = 255 - selection
    Image.fromarray(rgba, "RGBA").save(path)


def main() -> None:
    annotation = cv2.imread(str(ANNOTATION), cv2.IMREAD_COLOR)
    destination = cv2.imread(str(DESTINATION), cv2.IMREAD_COLOR)
    if annotation is None or destination is None:
        raise FileNotFoundError("The upright annotation page or destination image is missing")

    source_gray = cv2.cvtColor(annotation, cv2.COLOR_BGR2GRAY)
    destination_gray = cv2.cvtColor(destination, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(
        nfeatures=12000, scaleFactor=1.2, nlevels=8, edgeThreshold=19, fastThreshold=10
    )
    source_keys, source_desc = orb.detectAndCompute(source_gray, None)
    dest_keys, dest_desc = orb.detectAndCompute(destination_gray, None)
    matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(source_desc, dest_desc, k=2)
    good = [first for first, second in matches if first.distance < 0.72 * second.distance]
    if len(good) < 100:
        raise RuntimeError(f"Insufficient registration matches: {len(good)}")
    source_points = np.float32([source_keys[item.queryIdx].pt for item in good])
    destination_points = np.float32([dest_keys[item.trainIdx].pt for item in good])
    homography, inlier_mask = cv2.findHomography(
        source_points,
        destination_points,
        cv2.RANSAC,
        3.0,
        maxIters=10000,
        confidence=0.999,
    )
    if homography is None or inlier_mask is None:
        raise RuntimeError("Could not register the annotated scan")
    registered = cv2.warpPerspective(
        annotation,
        homography,
        (destination.shape[1], destination.shape[0]),
        flags=cv2.INTER_LANCZOS4,
    )
    cv2.imwrite(str(REGISTERED), registered, [cv2.IMWRITE_PNG_COMPRESSION, 3])

    hsv = cv2.cvtColor(registered, cv2.COLOR_BGR2HSV)
    red_raw = (
        ((hsv[:, :, 0] < 12) | (hsv[:, :, 0] > 172))
        & (hsv[:, :, 1] > 70)
        & (hsv[:, :, 2] > 50)
    ).astype(np.uint8) * 255
    yellow_raw = (
        (hsv[:, :, 0] >= 15)
        & (hsv[:, :, 0] <= 42)
        & (hsv[:, :, 1] > 55)
        & (hsv[:, :, 2] > 45)
    ).astype(np.uint8) * 255
    kernel = np.ones((5, 5), dtype=np.uint8)
    red_raw = cv2.morphologyEx(red_raw, cv2.MORPH_CLOSE, kernel)
    yellow_raw = cv2.morphologyEx(yellow_raw, cv2.MORPH_CLOSE, kernel)
    red, red_regions = filtered_components(red_raw)
    yellow, yellow_regions = filtered_components(yellow_raw)
    red = cv2.dilate(red, np.ones((5, 5), np.uint8), iterations=1)
    yellow = cv2.dilate(yellow, np.ones((5, 5), np.uint8), iterations=1)
    union = cv2.bitwise_or(red, yellow)
    cv2.imwrite(str(RED), red)
    cv2.imwrite(str(YELLOW), yellow)
    cv2.imwrite(str(UNION), union)
    rgba_edit_mask(red, RED_EDIT)
    rgba_edit_mask(yellow, YELLOW_EDIT)

    preview = destination.copy().astype(np.float32)
    yellow_overlay = np.zeros_like(destination, dtype=np.float32)
    yellow_overlay[:, :] = (0, 215, 255)
    red_overlay = np.zeros_like(destination, dtype=np.float32)
    red_overlay[:, :] = (0, 0, 255)
    yellow_alpha = (yellow.astype(np.float32) / 255.0 * 0.58)[:, :, None]
    red_alpha = (red.astype(np.float32) / 255.0 * 0.62)[:, :, None]
    preview = preview * (1.0 - yellow_alpha) + yellow_overlay * yellow_alpha
    preview = preview * (1.0 - red_alpha) + red_overlay * red_alpha
    cv2.imwrite(str(PREVIEW), np.clip(preview, 0, 255).astype(np.uint8))

    manifest = {
        "registration_matches": len(good),
        "registration_inliers": int(inlier_mask.sum()),
        "yellow_regions": yellow_regions,
        "red_regions": red_regions,
        "yellow_selected_pixels": int(np.count_nonzero(yellow)),
        "red_selected_pixels": int(np.count_nonzero(red)),
        "union_selected_pixels": int(np.count_nonzero(union)),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
