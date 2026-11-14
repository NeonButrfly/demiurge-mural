"""Local surface and hierarchy refinement of the accepted bridge mural."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/bridge_harmony/demiurge_bridge_harmonized.png"
OUT = ROOT / "outputs/bridge_refinement"
FINAL = OUT / "demiurge_bridge_refined.png"


def mask(size, shape, blur=0, polygon=False):
    result = Image.new("L", size)
    pen = ImageDraw.Draw(result)
    (pen.polygon if polygon else pen.ellipse)(shape, fill=255)
    if blur:
        result = result.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(result, dtype=np.float32) / 255


def line_mask(size, points, width, blur):
    result = Image.new("L", size)
    ImageDraw.Draw(result).line(points, fill=255, width=width, joint="curve")
    return np.asarray(result.filter(ImageFilter.GaussianBlur(blur)), dtype=np.float32) / 255


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source_rgb = Image.open(SOURCE).convert("RGB")
    src = source_rgb.convert("L")
    gray = np.asarray(src, dtype=np.float32)
    result = gray.copy()
    allowed = np.zeros(gray.shape, dtype=bool)

    def apply(delta, area):
        nonlocal result
        result = np.clip(result + delta * area, 0, 255)
        allowed[:] |= area > 0

    # 1. The existing trio gets the lower, more varied stone sheen seen nearby.
    trio = np.zeros(gray.shape, dtype=np.float32)
    trio[1120:1740, 1130:1780] = np.asarray(
        Image.open(ROOT / "outputs/mural_character_redesign/trio_sensual_mask.png").convert("L"),
        dtype=np.float32,
    ) / 255
    trio *= mask(src.size, (1165, 1215, 1720, 1685), 42)
    local = np.asarray(src.filter(ImageFilter.GaussianBlur(1.5)), dtype=np.float32)
    edge = gray - local
    rng = np.random.default_rng(376108)
    grain = np.uint8(np.clip(128 + rng.standard_normal(gray.shape) * 28, 0, 255))
    grain = np.asarray(Image.fromarray(grain).filter(ImageFilter.GaussianBlur(0.75)), dtype=np.float32)
    grain -= np.asarray(Image.fromarray(grain.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.0)), dtype=np.float32)
    grain /= max(float(np.std(grain)), 1e-6)
    smooth = np.clip((9 - np.abs(edge)) / 9, 0, 1)
    apply(-7 * np.clip((gray - 105) / 145, 0, 1) + 0.27 * edge + 3.7 * grain * smooth, trio)

    # Quiet the dark drapery's hard transition without covering its carving.
    canopy = mask(src.size, [(1185, 1190), (1235, 1198), (1300, 1220), (1350, 1270),
                              (1270, 1300), (1170, 1275)], 19, polygon=True)
    apply(5 * np.clip((95 - result) / 95, 0, 1), canopy)

    # 2. Separate Kharn's existing face and robe from similarly bright masonry.
    kharn_field = mask(src.size, (1595, 1540, 1890, 1940), 25)
    kharn_person = mask(src.size, [(1670, 1590), (1735, 1575), (1792, 1650),
                                    (1835, 1740), (1850, 1920), (1615, 1920),
                                    (1630, 1730)], 21, polygon=True)
    kharn_background = kharn_field * (1 - kharn_person)
    quiet_background = np.asarray(src.filter(ImageFilter.GaussianBlur(3.0)), dtype=np.float32) - result
    apply(-34 + 0.50 * quiet_background, kharn_background)
    contrast = np.clip((result - 112) * 0.24, -18, 25)
    apply(contrast + 17, kharn_person)
    face = mask(src.size, (1684, 1591, 1760, 1692), 12)
    apply(21 * np.clip((result - 65) / 150, 0, 1), face)

    # 3. Give the existing ruler/captive relationship a stronger value path.
    crown = mask(src.size, (690, 205, 1120, 640), 40)
    apply(np.clip((result - 120) * 0.12, -12, 19), crown)
    skull = mask(src.size, (806, 239, 955, 455), 24)
    crown_field = mask(src.size, (650, 170, 1150, 680), 45)
    apply(-10, crown_field * (1 - np.maximum(skull, crown * 0.40)))
    apply(np.clip((result - 112) * 0.27, -25, 31), skull)
    oracle = mask(src.size, (748, 1180, 1120, 1565), 35)
    oracle_field = mask(src.size, (640, 1120, 1190, 1620), 42)
    apply(-12, oracle_field * (1 - oracle))
    apply(np.clip((result - 112) * 0.17, -16, 23) + 5, oracle)
    left_chain = line_mask(src.size, [(683, 1335), (735, 1418), (813, 1470), (918, 1507)], 23, 15)
    right_chain = line_mask(src.size, [(994, 1490), (1083, 1427), (1159, 1373)], 22, 14)
    chains = np.maximum(left_chain, right_chain)
    apply(25 * np.clip((result - 65) / 140, 0, 1) - 6 * np.clip((90 - result) / 90, 0, 1), chains)

    rgb_result = np.clip(np.asarray(source_rgb, dtype=np.float32) +
                         (result - gray)[:, :, None], 0, 255).astype(np.uint8)
    refined = Image.fromarray(rgb_result)
    kharn_crop = (1530, 1480, 1940, 2000)
    kharn_qwen = Image.open(OUT / "kharn_face_qwen_candidate.png").convert("RGB")
    qwen_mask = Image.new("L", kharn_qwen.size)
    ImageDraw.Draw(qwen_mask).polygon(
        [(140, 90), (220, 75), (255, 130), (255, 220), (145, 235), (110, 165)], fill=255
    )
    qwen_mask = qwen_mask.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(10))
    portion = refined.crop(kharn_crop)
    portion.paste(kharn_qwen, (0, 0), qwen_mask)
    refined.paste(portion, kharn_crop[:2])
    allowed[kharn_crop[1]:kharn_crop[3], kharn_crop[0]:kharn_crop[2]] |= np.asarray(qwen_mask) > 0
    refined.save(FINAL)
    final = np.asarray(Image.open(FINAL).convert("RGB"), dtype=np.int16)
    previous = np.asarray(Image.open(SOURCE).convert("RGB"), dtype=np.int16)
    changed = np.any(final != previous, axis=2)
    validation = {
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(FINAL.read_bytes()).hexdigest(),
        "size_px": list(src.size),
        "changed_pixels": int(changed.sum()),
        "changed_outside_declared_masks": int(np.count_nonzero(changed & ~allowed)),
        "strong_color_pixels": int(np.count_nonzero(final.max(2) - final.min(2) > 60)),
        "new_figures_or_symbols": False,
        "kharn_face_generation_id": "3M51wq4seUCaHvj3cWj3GHZxjRA",
    }
    (OUT / "refinement_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["changed_outside_declared_masks"] or validation["strong_color_pixels"]:
        raise RuntimeError(validation)
    Image.open(FINAL).resize((512, 512), Image.Resampling.LANCZOS).save(OUT / "bridge_refined_512.png")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
