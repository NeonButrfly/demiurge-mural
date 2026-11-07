from pathlib import Path
from PIL import Image

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
base = Image.open(out / "demiurge_highlighted_anatomy_repaired_master.png").convert("RGB")

repairs = [
    ("white_a_midleft", (350, 650, 850, 1260), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-d27f1ffa-11f7-4ac1-ac67-f5da0af1f6f1.png")),
    ("white_b_lowerleft_angel", (80, 1160, 700, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-9210b5d2-4aea-446e-a038-286df3dd3ab1.png")),
    ("white_c_lowercenter", (430, 1420, 1080, 2048), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-b8e287ef-2ab5-42c7-978a-9fc127779375.png")),
    ("white_d_lowerright", (880, 1100, 1530, 1870), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-cfea1506-81c7-4608-a503-118181ec5422.png")),
]

for name, box, generated_path in repairs:
    x0, y0, x1, y1 = box
    size = (x1 - x0, y1 - y0)
    generated = Image.open(generated_path).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    original = base.crop(box)
    mask = Image.open(out / f"{name}_mask.png").convert("L")
    base.paste(Image.composite(generated, original, mask), (x0, y0))

destination = out / "demiurge_newmasks_white_body_pass.png"
base.save(destination)
print(destination)
