from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
base_img = Image.open(out / "demiurge_highlighted_anatomy_repaired_master.png").convert("RGB")
annotation_img = Image.open(r"C:\Users\Keifm\OneDrive\Desktop\newmasks.png").convert("RGB")
base = np.asarray(base_img, dtype=np.int16)
annotation = np.asarray(annotation_img, dtype=np.int16)
delta = annotation - base
denominator = np.maximum(255 - base, 1)
alpha = delta / denominator
white = (alpha.min(axis=2) > 0.12) & ((alpha.max(axis=2) - alpha.min(axis=2)) < 0.10)
white_mask = Image.fromarray((white * 255).astype(np.uint8))
white_mask = white_mask.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))
white_mask.save(out / "newmask_white_precise.png")

regions = {
    "white_a_midleft": (350, 650, 850, 1260),
    "white_b_lowerleft_angel": (80, 1160, 700, 2048),
    "white_c_lowercenter": (430, 1420, 1080, 2048),
    "white_d_lowerright": (880, 1100, 1530, 1870),
}

for name, box in regions.items():
    base_img.crop(box).save(out / f"{name}_clean.png")
    annotation_img.crop(box).save(out / f"{name}_annotated.png")
    white_mask.crop(box).save(out / f"{name}_mask.png")
    print(name, box)
