from pathlib import Path
from PIL import Image
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
base = Image.open(out / "demiurge_newmasks_white_green_pass.png").convert("RGB")

repairs = [
    ("r1_upper_left", (250, 380, 850, 950), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-7410e509-9dce-4d9f-9b12-1dd913fc566f.png")),
    ("r2_middle", (850, 1050, 1500, 1660), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-105cdb6b-2336-4c04-9ee8-28524176147d.png")),
    ("r3_lower_left", (0, 1300, 850, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-707dd08b-214d-4767-943b-a4d69881cacd.png")),
    ("r4_lower_right", (1250, 1200, 2048, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-30df75de-edcf-43c1-9493-decc798f7dc4.png")),
]

def match_tone(generated, original, mask):
    g = np.asarray(generated, dtype=np.float32)
    o = np.asarray(original, dtype=np.float32)
    m = np.asarray(mask, dtype=np.uint8) > 32
    if not m.any():
        return generated
    result = g.copy()
    for channel in range(3):
        source = g[..., channel][m]
        target = o[..., channel][m]
        source_std = max(float(source.std()), 1.0)
        target_std = max(float(target.std()), 1.0)
        result[..., channel] = (g[..., channel] - float(source.mean())) * (target_std / source_std) + float(target.mean())
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

for name, box, generated_path in repairs:
    x0, y0, x1, y1 = box
    size = (x1 - x0, y1 - y0)
    generated = Image.open(generated_path).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    original = base.crop(box)
    mask = Image.open(out / f"{name}_mask.png").convert("L")
    generated = match_tone(generated, original, mask)
    base.paste(Image.composite(generated, original, mask), (x0, y0))

destination = out / "demiurge_newmasks_completed.png"
base.save(destination)
print(destination)
