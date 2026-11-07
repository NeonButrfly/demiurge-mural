from pathlib import Path
from PIL import Image
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
base = Image.open(out / "demiurge_newmasks_completed.png").convert("RGB")

repairs = [
    ("fix_blue_eclipse", (340, 520, 620, 790), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-465ab229-903d-4ba6-8343-6673a64cd9c9.png")),
    ("fix_yellow_center", (600, 1160, 1050, 1660), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-7a72a241-0cb5-4eca-acb8-98edd5931d86.png")),
    ("fix_yellow_small", (570, 1680, 840, 1960), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-e87a4428-43b7-4156-8934-506df03b8c79.png")),
    ("fix_yellow_winged", (1120, 1380, 1570, 1810), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-cca6efeb-d60b-4a7f-98ed-4c9461da1b47.png")),
    ("fix_yellow_lowerright", (1480, 1580, 1880, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-3784d821-c545-4672-a957-01fa55fc91eb.png")),
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

destination = out / "demiurge_newmasks_fixed_bodies_eclipse.png"
base.save(destination)
print(destination)
