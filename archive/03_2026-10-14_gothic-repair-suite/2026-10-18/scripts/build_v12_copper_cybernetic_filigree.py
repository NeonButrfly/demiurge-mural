"""Add a copper-only cybernetic detail layer without replacing v11 artwork."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUTS = ROOT / "outputs"
BASE = OUTPUTS / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png"
REFERENCE = ASSETS / "references" / "Demiurge_Copper_Cybernetic_Reference_2048.png"
FINAL = OUTPUTS / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree.png"
OVERLAY = ASSETS / "generated" / "Pass7_v12_Copper_Cybernetic_Overlay.png"
MASK = ASSETS / "Pass7_v12_Copper_Cybernetic_Detail_Mask.png"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper_palette(reference: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    hsv = cv2.cvtColor(reference, cv2.COLOR_BGR2HSV)
    selected = (hsv[:, :, 0] >= 4) & (hsv[:, :, 0] <= 24) & (hsv[:, :, 1] >= 85)
    pixels = reference[selected]
    if len(pixels) < 100:
        return ((35, 75, 120), (45, 120, 190), (80, 175, 235))
    luminance = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).reshape(-1)
    colors = []
    for percentile in (25, 58, 88):
        index = int(np.argmin(np.abs(luminance - np.percentile(luminance, percentile))))
        colors.append(tuple(int(value) for value in pixels[index]))
    return tuple(colors)


def draw_trace(
    layer: np.ndarray,
    points: list[tuple[int, int]],
    palette: tuple[tuple[int, int, int], ...],
    closed: bool = False,
) -> None:
    pts = np.array(points, np.int32).reshape((-1, 1, 2))
    cv2.polylines(layer, [pts], closed, (*palette[0], 220), 3, cv2.LINE_AA)
    cv2.polylines(layer, [pts], closed, (*palette[1], 245), 2, cv2.LINE_AA)
    cv2.polylines(layer, [pts], closed, (*palette[2], 255), 1, cv2.LINE_AA)


def draw_port(
    layer: np.ndarray,
    center: tuple[int, int],
    radius: int,
    palette: tuple[tuple[int, int, int], ...],
) -> None:
    cv2.circle(layer, center, radius + 1, (*palette[0], 225), -1, cv2.LINE_AA)
    cv2.circle(layer, center, radius, (*palette[2], 255), 1, cv2.LINE_AA)
    cv2.circle(layer, center, max(radius - 2, 1), (12, 18, 24, 240), -1, cv2.LINE_AA)
    cv2.circle(layer, center, 1, (*palette[2], 255), -1, cv2.LINE_AA)


def draw_bands(
    layer: np.ndarray,
    centers: list[tuple[int, int]],
    angle_degrees: float,
    half_length: int,
    palette: tuple[tuple[int, int, int], ...],
) -> None:
    angle = np.deg2rad(angle_degrees)
    dx = int(round(np.cos(angle) * half_length))
    dy = int(round(np.sin(angle) * half_length))
    for x, y in centers:
        draw_trace(layer, [(x - dx, y - dy), (x + dx, y + dy)], palette)


def draw_arc(
    layer: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    start: float,
    end: float,
    palette: tuple[tuple[int, int, int], ...],
    rotation: float = 0,
) -> None:
    cv2.ellipse(layer, center, axes, rotation, start, end, (*palette[0], 220), 3, cv2.LINE_AA)
    cv2.ellipse(layer, center, axes, rotation, start, end, (*palette[1], 245), 2, cv2.LINE_AA)
    cv2.ellipse(layer, center, axes, rotation, start, end, (*palette[2], 255), 1, cv2.LINE_AA)


def add_relief_copper(
    layer: np.ndarray,
    base: np.ndarray,
    palette: tuple[tuple[int, int, int], ...],
) -> None:
    """Tint only existing engraved relief edges inside curated mechanical zones."""
    region = np.zeros(base.shape[:2], np.uint8)
    # Existing halo metalwork only. Stroke masks avoid tinting heads and faces.
    cv2.ellipse(region, (489, 84), (91, 88), 0, 0, 360, 255, 14)
    cv2.ellipse(region, (421, 121), (67, 67), 0, 0, 360, 255, 12)
    cv2.ellipse(region, (486, 111), (30, 42), 0, 0, 360, 0, -1)
    cv2.ellipse(region, (413, 143), (31, 40), 0, 0, 360, 0, -1)
    cv2.fillPoly(region, [np.array([(700, 20), (873, 5), (956, 85), (935, 178), (816, 150)], np.int32)], 255)
    # Demon arm/torso harness, but not its head.
    cv2.fillPoly(region, [np.array([(760, 52), (834, 18), (846, 107), (792, 252), (735, 213)], np.int32)], 255)
    # Hooded mechanical forearm and the ram/skull machinery below the central robes.
    cv2.fillPoly(region, [np.array([(272, 548), (333, 550), (445, 577), (438, 634), (325, 621)], np.int32)], 255)
    cv2.fillPoly(region, [np.array([(426, 468), (520, 458), (590, 596), (548, 670), (451, 608)], np.int32)], 255)
    # Keep the central reclining face out of the machinery treatment.
    cv2.circle(region, (476, 582), 45, 0, -1)
    # Selected robe/cybernetic relief on the lower reclining figure. The head,
    # exposed arms, and adjacent figures stay outside the edge treatment.
    cv2.fillPoly(region, [np.array([(690, 905), (776, 887), (901, 956), (949, 1056), (836, 1081), (717, 1001)], np.int32)], 255)
    cv2.circle(region, (711, 865), 48, 0, -1)
    cv2.circle(region, (822, 906), 38, 0, -1)

    gray = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 78, 178, L2gradient=True)
    # One-pixel engraved accents plus a soft adjacent glint; never replace source detail.
    fine = cv2.bitwise_and(edges, region)
    soft = cv2.dilate(fine, np.ones((2, 2), np.uint8), iterations=1)
    soft = cv2.bitwise_and(soft, cv2.bitwise_not(fine))
    layer[soft > 0, :3] = palette[0]
    layer[soft > 0, 3] = np.maximum(layer[soft > 0, 3], 72)
    layer[fine > 0, :3] = palette[2]
    layer[fine > 0, 3] = np.maximum(layer[fine > 0, 3], 145)


def build_overlay(base: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    height, width = base.shape[:2]
    if (width, height) != (1131, 1131):
        raise AssertionError(f"Unexpected v11 dimensions: {width}x{height}")
    palette = copper_palette(reference)
    layer = np.zeros((height, width, 4), np.uint8)

    # Start with copper glints that inherit the destination's own engraved geometry.
    add_relief_copper(layer, base, palette)

    # Upper-right demon: contour-following conduits and wing-root hardware.
    draw_trace(layer, [(735, 132), (754, 157), (771, 187), (778, 216), (774, 239)], palette)
    draw_trace(layer, [(782, 130), (796, 103), (807, 73), (812, 44)], palette)
    draw_port(layer, (754, 157), 5, palette)
    draw_port(layer, (813, 55), 4, palette)
    draw_arc(layer, (829, 82), (23, 17), 165, 338, palette, rotation=-12)
    # Short wing-root inlays follow the membrane ribs; they do not redraw the wing.
    for endpoint in ((920, 79), (943, 108), (934, 139)):
        draw_trace(layer, [(844, 85), endpoint], palette)

    # Central robes: fine circuitry following existing folds rather than bodies.
    draw_trace(layer, [(443, 237), (470, 267), (501, 307), (524, 355), (548, 405)], palette)
    draw_trace(layer, [(503, 194), (534, 224), (558, 262), (579, 302)], palette)
    for center in ((475, 271), (522, 355), (560, 264)):
        draw_port(layer, center, 4, palette)

    # Hooded cybernetic arm: segmented copper conduit with joint collars.
    draw_trace(layer, [(302, 584), (334, 590), (369, 602), (406, 603), (431, 592)], palette)
    draw_bands(layer, [(326, 589), (347, 596), (371, 601), (397, 603), (420, 597)], 104, 8, palette)
    draw_port(layer, (301, 583), 5, palette)
    draw_port(layer, (372, 602), 4, palette)

    # Ram skull machinery and adjoining feather relief.
    draw_arc(layer, (490, 511), (38, 26), 220, 490, palette, rotation=-18)
    draw_port(layer, (500, 526), 4, palette)
    draw_trace(layer, [(504, 531), (527, 551), (548, 577), (560, 604)], palette)

    # Spear bearer: collars, a slim torso trace, and segmented spear inlays.
    draw_port(layer, (711, 716), 4, palette)
    draw_trace(layer, [(711, 716), (733, 742), (746, 779), (755, 813)], palette)
    draw_trace(layer, [(774, 680), (731, 720), (688, 762), (646, 806)], palette)
    draw_bands(layer, [(747, 706), (716, 736), (686, 766)], 43, 7, palette)

    # V11 reclining figure: robe filigree only; face, hands, and anatomy untouched.
    draw_trace(layer, [(701, 873), (732, 899), (766, 930), (799, 960), (833, 988), (867, 1010)], palette)
    draw_trace(layer, [(745, 853), (772, 875), (800, 901), (825, 929)], palette)
    draw_arc(layer, (777, 923), (25, 15), 28, 328, palette, rotation=26)
    draw_arc(layer, (836, 979), (28, 17), 32, 326, palette, rotation=28)
    for center in ((732, 899), (799, 960), (866, 1010)):
        draw_port(layer, center, 4, palette)

    # Small skull-machine ports distributed through the lower relief.
    for center in ((222, 1001), (487, 1034), (690, 1091), (982, 948), (962, 1110)):
        draw_port(layer, center, 3, palette)

    alpha = layer[:, :, 3]
    # Let the copper inherit local relief shading without altering underlying geometry.
    luminance = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    modulation = np.clip(0.82 + luminance * 0.30, 0.82, 1.0)
    layer[:, :, :3] = np.clip(layer[:, :, :3].astype(np.float32) * modulation[:, :, None], 0, 255).astype(np.uint8)
    return layer, (alpha > 0).astype(np.uint8) * 255


def details(image: np.ndarray) -> np.ndarray:
    crops = [
        image[0:315, 320:1070],
        image[490:760, 235:845],
        image[720:1131, 180:1080],
    ]
    thumbs = [cv2.resize(crop, (760, 340), interpolation=cv2.INTER_LANCZOS4) for crop in crops]
    return np.vstack(thumbs)


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    reference = cv2.imread(str(REFERENCE), cv2.IMREAD_COLOR)
    if base is None or reference is None:
        raise FileNotFoundError("V11 destination or copper reference missing")
    layer, detail_mask = build_overlay(base, reference)
    save(OVERLAY, layer)
    save(MASK, detail_mask)

    alpha = layer[:, :, 3].astype(np.float32) / 255.0
    alpha3 = alpha[:, :, None]
    result = np.clip(
        base.astype(np.float32) * (1.0 - alpha3) + layer[:, :, :3].astype(np.float32) * alpha3,
        0,
        255,
    ).astype(np.uint8)
    save(FINAL, result)

    changed = np.any(base != result, axis=2)
    violations = changed & (detail_mask == 0)
    difference = cv2.absdiff(base, result)
    difference_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree_Difference.png"
    out_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree_OutOfMask.png"
    details_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree_Details.png"
    save(difference_path, cv2.convertScaleAbs(difference, alpha=3.0))
    violation_view = np.zeros_like(result)
    violation_view[violations] = (0, 0, 255)
    save(out_path, violation_view)
    save(details_path, details(result))

    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
    copper = changed & (hsv[:, :, 0] >= 3) & (hsv[:, :, 0] <= 26) & (hsv[:, :, 1] >= 55)
    report = {
        "issue": 14,
        "base": str(BASE.relative_to(ROOT)),
        "base_sha256": sha256(BASE),
        "reference": str(REFERENCE.relative_to(ROOT)),
        "reference_sha256": sha256(REFERENCE),
        "final": str(FINAL.relative_to(ROOT)),
        "final_sha256": sha256(FINAL),
        "dimensions": [int(result.shape[1]), int(result.shape[0])],
        "overlay_pixels": int(np.count_nonzero(detail_mask)),
        "changed_pixels": int(np.count_nonzero(changed)),
        "copper_pixels": int(np.count_nonzero(copper)),
        "changed_pixels_outside_overlay": int(np.count_nonzero(violations)),
        "outside_overlay_byte_identical": bool(np.count_nonzero(violations) == 0),
        "method": "reference-derived copper palette with deterministic non-replacement cybernetic overlay",
    }
    qa_path = OUTPUTS / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    archive = OUTPUTS / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL,
            OVERLAY,
            MASK,
            difference_path,
            out_path,
            details_path,
            qa_path,
            ROOT / "docs" / "prompts" / "v12-copper-cybernetic-filigree.md",
        ):
            bundle.write(path, path.relative_to(ROOT))

    if np.count_nonzero(violations):
        raise AssertionError("A pixel changed outside the copper overlay")
    if report["copper_pixels"] < 2_000:
        raise AssertionError("Copper detail layer is unexpectedly sparse")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
