"""Apply restrained local value changes and the approved trio edge repair.

The source geometry and figures are preserved. Only the named masks are edited.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "outputs" / "mural_character_redesign"
OUT = ROOT / "outputs" / "bridge_harmony"
SOURCE = WORK / "demiurge_bridge_mericanai_original_demon.png"
FINAL = OUT / "demiurge_bridge_harmonized.png"


def shape_mask(size: tuple[int, int], shape, blur: int, kind: str = "ellipse") -> np.ndarray:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    if kind == "ellipse":
        draw.ellipse(shape, fill=255)
    else:
        draw.polygon(shape, fill=255)
    return np.asarray(mask.filter(ImageFilter.GaussianBlur(blur)), dtype=np.float32) / 255


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE).convert("RGB")
    result = np.asarray(image, dtype=np.float32).copy()

    def apply(delta: np.ndarray, mask: np.ndarray) -> None:
        nonlocal result
        result = np.clip(result + delta[:, :, None] * mask[:, :, None], 0, 255)

    # Let the existing upper central skull and spoked ring lead at distance.
    luminance = result.mean(2)
    axis = shape_mask(image.size, (645, 170, 1155, 665), 60)
    apply(np.clip((luminance - 120) * .12, -15, 17), axis)

    # Compress the smooth highlights on the bound oracle and retain engravings.
    luminance = result.mean(2)
    oracle = np.zeros((2048, 2048), np.float32)
    oracle[1130:1700, 600:1290] = np.asarray(Image.open(WORK / "cyan_composite_mask.png").convert("L"), dtype=np.float32) / 255
    oracle *= shape_mask(image.size, (700, 1160, 1240, 1680), 45)
    blurred = np.asarray(Image.fromarray(np.uint8(luminance)).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32)
    apply(-14 * np.clip((luminance - 105) / 150, 0, 1) + .19 * (luminance - blurred), oracle)

    # Reveal midtones in the scribe's near-black robes.
    luminance = result.mean(2)
    scribe = shape_mask(image.size, [(731, 1126), (814, 1120), (871, 1170), (897, 1252), (910, 1400), (828, 1450), (739, 1370), (705, 1240)], 15, "polygon")
    apply(18 * np.clip((100 - luminance) / 100, 0, 1) ** 1.5, scribe)

    # Place the trio's skin and fabric highlights in the surrounding value range.
    luminance = result.mean(2)
    trio = np.zeros((2048, 2048), np.float32)
    trio[1120:1740, 1130:1780] = np.asarray(Image.open(WORK / "trio_sensual_mask.png").convert("L"), dtype=np.float32) / 255
    trio *= shape_mask(image.size, (1170, 1180, 1720, 1710), 50)
    blurred = np.asarray(Image.fromarray(np.uint8(luminance)).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32)
    apply(-11 * np.clip((luminance - 115) / 140, 0, 1) + .14 * (luminance - blurred), trio)

    # Separate Kharn Sagara's existing face and upper robe without new symbols.
    luminance = result.mean(2)
    kharn = shape_mask(image.size, (1635, 1530, 1860, 1810), 35)
    apply(np.clip((luminance - 105) * .09, -8, 11), kharn)

    toned = Image.fromarray(np.uint8(np.clip(result, 0, 255)))
    box = (1120, 1170, 1340, 1660)
    seam = Image.open(OUT / "trio_left_seam_qwen.png").convert("RGB")
    seam_mask = Image.open(OUT / "trio_left_seam_mask.png").filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(7))
    portion = toned.crop(box)
    portion.paste(seam, (0, 0), seam_mask)
    toned.paste(portion, box[:2])
    toned.save(FINAL)
    final = np.asarray(toned)
    original = np.asarray(image)
    changed = np.any(final != original, axis=2)
    allowed = (axis > 0) | (oracle > 0) | (scribe > 0) | (trio > 0) | (kharn > 0)
    seam_allowed = np.zeros(allowed.shape, dtype=bool)
    seam_allowed[box[1]:box[3], box[0]:box[2]] = np.asarray(seam_mask) > 0
    outside = int(np.count_nonzero(changed & ~(allowed | seam_allowed)))
    chroma = final.astype(np.int16).max(2) - final.astype(np.int16).min(2)
    validation = {
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(FINAL.read_bytes()).hexdigest(),
        "size_px": list(image.size),
        "changed_pixels": int(changed.sum()),
        "changed_outside_declared_masks": outside,
        "strong_color_pixels": int(np.count_nonzero(chroma > 60)),
        "seam_generation_id": "3M4jdEm2lHDinvVst5wkM1twZyV",
    }
    (OUT / "bridge_harmony_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if outside:
        raise RuntimeError(f"{outside} pixels changed outside declared masks")
    print(FINAL)


if __name__ == "__main__":
    main()
