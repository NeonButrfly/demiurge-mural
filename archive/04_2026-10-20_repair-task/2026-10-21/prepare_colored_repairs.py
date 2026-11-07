from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
annotation_img = Image.open(r"C:\Users\Keifm\OneDrive\Desktop\newmasks.png").convert("RGB")
reference_img = Image.open(out / "demiurge_highlighted_anatomy_repaired_master.png").convert("RGB")
working_img = Image.open(out / "demiurge_newmasks_white_body_pass.png").convert("RGB")
annotation = np.asarray(annotation_img, dtype=np.float32)
reference = np.asarray(reference_img, dtype=np.float32)
delta = annotation - reference

eps = 1.0
red_alpha = np.stack([
    delta[..., 0] / np.maximum(255 - reference[..., 0], eps),
    -delta[..., 1] / np.maximum(reference[..., 1], eps),
    -delta[..., 2] / np.maximum(reference[..., 2], eps),
], axis=2)
green_alpha = np.stack([
    -delta[..., 0] / np.maximum(reference[..., 0], eps),
    delta[..., 1] / np.maximum(255 - reference[..., 1], eps),
    -delta[..., 2] / np.maximum(reference[..., 2], eps),
], axis=2)

red = ((annotation[..., 0] - annotation[..., 1]) > 55) & ((annotation[..., 0] - annotation[..., 2]) > 35) & (annotation[..., 0] > 95)
green = ((annotation[..., 1] - annotation[..., 0]) > 35) & ((annotation[..., 1] - annotation[..., 2]) > 30) & (annotation[..., 1] > 80)

def clean(raw):
    mask = Image.fromarray((raw * 255).astype(np.uint8))
    return mask.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))

green_mask = clean(green)
red_mask = clean(red)
green_mask.save(out / "newmask_green_precise.png")
red_mask.save(out / "newmask_red_precise.png")

regions = {
    "green_a_midleft": (430, 650, 790, 1280),
    "green_b_midright": (820, 820, 1090, 1110),
    "green_c_lowerleft": (150, 1430, 680, 1750),
    "green_d_lowerright": (1120, 1260, 1510, 1810),
    "red_a_upperleft": (180, 300, 700, 780),
    "red_b_midright": (760, 820, 1230, 1330),
    "red_c_lowerleft": (0, 1040, 700, 1760),
    "red_d_lowerright": (900, 940, 1690, 1750),
    "red_e_bottom": (300, 1430, 2048, 2048),
}

for name, box in regions.items():
    working_img.crop(box).save(out / f"{name}_clean.png")
    annotation_img.crop(box).save(out / f"{name}_annotated.png")
    (green_mask if name.startswith("green") else red_mask).crop(box).save(out / f"{name}_mask.png")

