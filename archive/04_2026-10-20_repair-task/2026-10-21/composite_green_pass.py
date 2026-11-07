from pathlib import Path
from PIL import Image
import numpy as np

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
base = Image.open(out / "demiurge_newmasks_white_body_pass.png").convert("RGB")

repairs = [
    ("g1_shoulder", (600, 850, 850, 1080), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-1796b577-f1b9-4d32-97aa-2498061d59dc.png")),
    ("g2_center_body", (620, 1180, 1040, 1640), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-0ff65be6-06ac-436a-84c6-9c3f9b496e65.png")),
    ("g3_hand", (1050, 1030, 1320, 1330), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-13342f7a-d45b-41e3-900b-3ae29109ccd7.png")),
    ("g4_bottom_faces", (150, 1820, 700, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-0966cf9a-5ef7-4bc4-a0b6-9c0e88f953aa.png")),
    ("g5_lower_right", (1350, 1500, 1900, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-91f7a45a-fd04-41b7-97da-43041269ed6d.png")),
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

destination = out / "demiurge_newmasks_white_green_pass.png"
base.save(destination)
print(destination)
