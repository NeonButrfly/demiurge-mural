"""Build visible copper cybernetic hardware on v11 without replacing its artwork."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png"
REFERENCE = ROOT / "assets" / "references" / "Demiurge_Copper_Cybernetic_Reference_2048.png"
FINAL = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics.png"
OVERLAY = ROOT / "assets" / "generated" / "Pass7_v13_Actual_Copper_Cybernetics_Overlay.png"
MASK = ROOT / "assets" / "Pass7_v13_Actual_Copper_Cybernetics_Mask.png"


def save(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3]):
        raise OSError(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def palette_from(reference: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    hsv = cv2.cvtColor(reference, cv2.COLOR_BGR2HSV)
    selected = (hsv[:, :, 0] >= 4) & (hsv[:, :, 0] <= 24) & (hsv[:, :, 1] >= 80)
    pixels = reference[selected]
    gray = cv2.cvtColor(pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).reshape(-1)
    colors = []
    for q in (18, 52, 88):
        target = np.percentile(gray, q)
        colors.append(tuple(int(v) for v in pixels[np.argmin(np.abs(gray - target))]))
    return tuple(colors)


def plate(
    layer: np.ndarray,
    points: list[tuple[int, int]],
    colors: tuple[tuple[int, int, int], ...],
    rivets: bool = True,
) -> None:
    pts = np.array(points, np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(layer, [pts], (*colors[0], 152), cv2.LINE_AA)
    cv2.polylines(layer, [pts], True, (8, 12, 16, 205), 6, cv2.LINE_AA)
    cv2.polylines(layer, [pts], True, (*colors[1], 255), 4, cv2.LINE_AA)
    cv2.polylines(layer, [pts], True, (*colors[2], 255), 1, cv2.LINE_AA)
    center = np.mean(np.array(points, np.float32), axis=0)
    inner = center + (np.array(points, np.float32) - center) * 0.78
    cv2.polylines(layer, [inner.astype(np.int32).reshape((-1, 1, 2))], True, (*colors[2], 180), 1, cv2.LINE_AA)
    if rivets:
        for x, y in points[:: max(1, len(points) // 4)]:
            cv2.circle(layer, (x, y), 4, (7, 10, 13, 250), -1, cv2.LINE_AA)
            cv2.circle(layer, (x, y), 3, (*colors[2], 255), 1, cv2.LINE_AA)


def ellipse_points(center: tuple[int, int], axes: tuple[int, int], angle: int) -> list[tuple[int, int]]:
    points = cv2.ellipse2Poly(center, axes, angle, 0, 360, 12)
    return [tuple(int(v) for v in point) for point in points]


def collar(
    layer: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    angle: int,
    colors: tuple[tuple[int, int, int], ...],
) -> None:
    for expand, color, width, alpha in (
        (5, (7, 10, 14), 8, 245),
        (2, colors[0], 6, 245),
        (0, colors[1], 4, 255),
        (-2, colors[2], 1, 255),
    ):
        pts = cv2.ellipse2Poly(center, (axes[0] + expand, axes[1] + expand), angle, 0, 360, 8)
        cv2.polylines(layer, [pts.reshape((-1, 1, 2))], True, (*color, alpha), width, cv2.LINE_AA)


def port(
    layer: np.ndarray,
    center: tuple[int, int],
    radius: int,
    colors: tuple[tuple[int, int, int], ...],
) -> None:
    cv2.circle(layer, center, radius + 5, (6, 9, 12, 245), -1, cv2.LINE_AA)
    cv2.circle(layer, center, radius + 3, (*colors[0], 245), -1, cv2.LINE_AA)
    cv2.circle(layer, center, radius + 2, (*colors[2], 255), 2, cv2.LINE_AA)
    cv2.circle(layer, center, max(3, radius - 3), (8, 12, 17, 255), -1, cv2.LINE_AA)
    cv2.circle(layer, center, 2, (*colors[2], 255), -1, cv2.LINE_AA)
    for angle in (45, 135, 225, 315):
        rad = np.deg2rad(angle)
        x = int(center[0] + np.cos(rad) * (radius + 1))
        y = int(center[1] + np.sin(rad) * (radius + 1))
        cv2.circle(layer, (x, y), 1, (*colors[2], 255), -1, cv2.LINE_AA)


def cable(
    layer: np.ndarray,
    points: list[tuple[int, int]],
    colors: tuple[tuple[int, int, int], ...],
) -> None:
    pts = np.array(points, np.int32).reshape((-1, 1, 2))
    cv2.polylines(layer, [pts], False, (4, 7, 10, 240), 10, cv2.LINE_AA)
    cv2.polylines(layer, [pts], False, (*colors[0], 245), 7, cv2.LINE_AA)
    cv2.polylines(layer, [pts], False, (*colors[1], 255), 4, cv2.LINE_AA)
    cv2.polylines(layer, [pts], False, (*colors[2], 235), 1, cv2.LINE_AA)


def segmented_plate(
    layer: np.ndarray,
    points: list[tuple[int, int]],
    colors: tuple[tuple[int, int, int], ...],
    cuts: list[tuple[tuple[int, int], tuple[int, int]]],
) -> None:
    plate(layer, points, colors)
    for start, end in cuts:
        cv2.line(layer, start, end, (5, 8, 12, 245), 5, cv2.LINE_AA)
        cv2.line(layer, start, end, (*colors[2], 230), 1, cv2.LINE_AA)


def build(base: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    colors = palette_from(reference)
    layer = np.zeros((*base.shape[:2], 4), np.uint8)

    # Upper-right demon: fitted shoulder mechanism, rib harness, wing-root hub.
    plate(layer, ellipse_points((793, 132), (35, 19), -58), colors)
    port(layer, (793, 132), 8, colors)
    segmented_plate(layer, [(741, 165), (771, 149), (793, 176), (786, 211), (759, 226), (738, 202)], colors,
                    [((752, 173), (784, 187)), ((748, 195), (782, 205))])
    collar(layer, (813, 67), (19, 10), -70, colors)
    cable(layer, [(793, 132), (808, 110), (817, 88), (813, 67)], colors)
    port(layer, (760, 195), 7, colors)
    cable(layer, [(760, 195), (775, 221), (777, 246)], colors)
    plate(layer, ellipse_points((839, 82), (27, 15), -7), colors)
    for end in ((902, 78), (919, 101), (914, 127)):
        cable(layer, [(843, 83), end], colors)

    # Hooded figure: an unmistakable articulated copper gauntlet over the existing arm.
    segmented_plate(layer, [(300, 559), (336, 563), (377, 576), (425, 588), (438, 606),
                            (420, 622), (370, 613), (324, 599), (296, 580)], colors,
                    [((326, 564), (318, 597)), ((353, 569), (345, 605)),
                     ((383, 578), (375, 614)), ((412, 587), (402, 617))])
    collar(layer, (300, 578), (13, 21), -8, colors)
    collar(layer, (430, 604), (10, 19), -72, colors)
    port(layer, (369, 592), 8, colors)

    # Central machinery: skull/ram housing with connected copper vertebrae.
    plate(layer, ellipse_points((493, 516), (34, 29), -8), colors)
    port(layer, (493, 516), 8, colors)
    cable(layer, [(499, 529), (518, 551), (536, 577), (548, 603)], colors)
    for center in ((518, 551), (535, 577), (548, 603)):
        collar(layer, center, (10, 5), 48, colors)

    # Spear-bearer: a functional forearm bracer and mechanically clamped grip.
    segmented_plate(layer, [(699, 716), (716, 695), (748, 699), (774, 717), (766, 741),
                            (735, 744), (708, 735)], colors,
                    [((718, 700), (714, 738)), ((741, 701), (736, 743)), ((759, 709), (753, 740))])
    collar(layer, (704, 724), (11, 18), 35, colors)
    port(layer, (742, 720), 7, colors)
    collar(layer, (775, 714), (9, 16), 42, colors)

    # Lower reclining figure: solid copper corset and hip machinery on the existing robe.
    segmented_plate(layer, [(710, 882), (729, 866), (753, 870), (775, 888), (780, 914),
                            (763, 929), (738, 925), (717, 907)], colors,
                    [((728, 875), (769, 899)), ((721, 895), (774, 912))])
    port(layer, (747, 899), 8, colors)
    plate(layer, ellipse_points((815, 963), (31, 19), 28), colors)
    port(layer, (815, 963), 7, colors)
    cable(layer, [(756, 907), (782, 934), (815, 963)], colors)
    cable(layer, [(823, 969), (846, 987), (869, 1002)], colors)

    # Smaller, clearly attached implants on existing lower bodies.
    plate(layer, ellipse_points((303, 838), (23, 13), 38), colors)
    port(layer, (303, 838), 6, colors)
    cable(layer, [(303, 838), (320, 851), (332, 866)], colors)
    plate(layer, ellipse_points((407, 904), (21, 12), 22), colors)
    port(layer, (407, 904), 6, colors)
    cable(layer, [(407, 904), (425, 918), (438, 936)], colors)
    plate(layer, ellipse_points((982, 948), (20, 12), -30), colors)
    port(layer, (982, 948), 6, colors)

    alpha = layer[:, :, 3]
    # Preserve engraved relief modulation so the hardware sits in the same lighting.
    light = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    factor = np.clip(0.76 + 0.34 * light, 0.76, 1.0)
    layer[:, :, :3] = np.clip(layer[:, :, :3].astype(np.float32) * factor[:, :, None], 0, 255).astype(np.uint8)
    return layer, (alpha > 0).astype(np.uint8) * 255


def montage(image: np.ndarray) -> np.ndarray:
    crops = [image[0:280, 680:970], image[515:660, 265:465], image[655:785, 675:805], image[815:1090, 650:980]]
    tiles = [cv2.resize(crop, (520, 300), interpolation=cv2.INTER_LANCZOS4) for crop in crops]
    return np.vstack(tiles)


def main() -> None:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    reference = cv2.imread(str(REFERENCE), cv2.IMREAD_COLOR)
    if base is None or reference is None:
        raise FileNotFoundError("v11 destination or copper reference missing")
    layer, mask = build(base, reference)
    alpha = layer[:, :, 3].astype(np.float32)[:, :, None] / 255.0
    final = np.clip(base.astype(np.float32) * (1 - alpha) + layer[:, :, :3].astype(np.float32) * alpha, 0, 255).astype(np.uint8)
    save(OVERLAY, layer)
    save(MASK, mask)
    save(FINAL, final)

    changed = np.any(base != final, axis=2)
    violations = changed & (mask == 0)
    difference = cv2.absdiff(base, final)
    diff_path = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics_Difference.png"
    out_path = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics_OutOfMask.png"
    details_path = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics_Details.png"
    save(diff_path, cv2.convertScaleAbs(difference, alpha=2.5))
    out = np.zeros_like(final)
    out[violations] = (0, 0, 255)
    save(out_path, out)
    save(details_path, montage(final))

    hsv = cv2.cvtColor(final, cv2.COLOR_BGR2HSV)
    copper = changed & (hsv[:, :, 0] >= 3) & (hsv[:, :, 0] <= 27) & (hsv[:, :, 1] >= 55)
    report = {
        "issue": 14,
        "base": str(BASE.relative_to(ROOT)),
        "base_sha256": sha256(BASE),
        "reference": str(REFERENCE.relative_to(ROOT)),
        "reference_role": "palette and mechanical vocabulary only; no donor replacement",
        "final": str(FINAL.relative_to(ROOT)),
        "final_sha256": sha256(FINAL),
        "dimensions": [final.shape[1], final.shape[0]],
        "overlay_pixels": int(np.count_nonzero(mask)),
        "changed_pixels": int(np.count_nonzero(changed)),
        "copper_pixels": int(np.count_nonzero(copper)),
        "changed_pixels_outside_overlay": int(np.count_nonzero(violations)),
        "outside_overlay_byte_identical": not np.any(violations),
        "components": ["fitted plates", "bolted ports", "joint collars", "attached conduits", "segmented gauntlet", "mechanical spear clamp"],
    }
    qa_path = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics_QA.json"
    qa_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    archive = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics_Deliverables.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in (
            FINAL, OVERLAY, MASK, diff_path, out_path, details_path, qa_path,
            ROOT / "docs" / "prompts" / "v13-actual-cybernetics.md",
        ):
            bundle.write(path, path.relative_to(ROOT))
    if np.any(violations):
        raise AssertionError("pixel changed outside hardware overlay")
    if report["copper_pixels"] < 25_000:
        raise AssertionError("actual cybernetic hardware is too sparse")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
