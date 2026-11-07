from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
working = Image.open(out / "demiurge_newmasks_completed.png").convert("RGB")
annotation = Image.open(r"C:\Users\Keifm\OneDrive\Desktop\demiurge_newmasks_fixes.png").convert("RGB")
a = np.asarray(annotation, dtype=np.int16)

yellow = (a[..., 0] > 110) & (a[..., 1] > 90) & ((a[..., 0] - a[..., 2]) > 35) & ((a[..., 1] - a[..., 2]) > 20)
blue = (a[..., 2] > 85) & ((a[..., 2] - a[..., 0]) > 20) & ((a[..., 2] - a[..., 1]) > 8)

def clean(raw, size=5):
    mask = Image.fromarray((raw * 255).astype(np.uint8))
    return mask.filter(ImageFilter.MinFilter(size)).filter(ImageFilter.MaxFilter(size + 4)).filter(ImageFilter.GaussianBlur(1.2))

yellow_mask = clean(yellow)
blue_mask = clean(blue, 3)
yellow_mask.save(out / "fixmask_yellow.png")
blue_mask.save(out / "fixmask_blue.png")

regions = {
    "fix_blue_eclipse": (340, 520, 620, 790),
    "fix_yellow_center": (600, 1160, 1050, 1660),
    "fix_yellow_small": (570, 1680, 840, 1960),
    "fix_yellow_winged": (1120, 1380, 1570, 1810),
    "fix_yellow_lowerright": (1480, 1580, 1880, 2048),
}

for name, box in regions.items():
    working.crop(box).save(out / f"{name}_clean.png")
    annotation.crop(box).save(out / f"{name}_annotated.png")
    (blue_mask if "blue" in name else yellow_mask).crop(box).save(out / f"{name}_mask.png")
