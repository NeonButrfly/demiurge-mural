from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
annotation = np.asarray(Image.open(r"C:\Users\Keifm\OneDrive\Desktop\newmasks.png").convert("RGB"), dtype=np.int16)
base = np.asarray(Image.open(out / "demiurge_highlighted_anatomy_repaired_master.png").convert("RGB"), dtype=np.int16)
delta = annotation - base

red = (delta[..., 0] > 28) & ((delta[..., 0] - delta[..., 1]) > 25) & ((delta[..., 0] - delta[..., 2]) > 12)
green = (delta[..., 1] > 28) & ((delta[..., 1] - delta[..., 0]) > 25) & ((delta[..., 1] - delta[..., 2]) > 20)
white = (delta.min(axis=2) > 22) & ((delta.max(axis=2) - delta.min(axis=2)) < 70) & ~red & ~green

for name, raw in (("white", white), ("green", green), ("red", red)):
    mask = Image.fromarray((raw * 255).astype(np.uint8))
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    mask.save(out / f"newmask_{name}.png")
    ys, xs = np.where(raw)
    print(name, int(raw.sum()), (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
