from PIL import Image, ImageFilter
from pathlib import Path

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
base = Image.open(out / "demiurge_highlight_repairs_intermediate2.png").convert("RGB")
mask_full = Image.open(out / "demiurge_highlight_repair_mask.png").convert("L")

repairs = [
    ((740, 1030, 980, 1200), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-6e25b9ff-8a02-4e76-9ec7-430fbb54a2d4.png")),
    ((1020, 1100, 1450, 1420), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-f8772ada-61bb-4d81-adf8-48e0284e35e4.png")),
    ((300, 1240, 820, 1660), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-e896830b-67c4-4754-b728-f05c78393b69.png")),
    ((930, 1360, 1600, 1660), Path(r"C:\Users\Keifm\.codex\generated_images\01a15a97-5bc0-7f31-a5d7-7c3dd4b69193\exec-1cfa3769-fd0f-4677-96d4-505319bcff98.png")),
]

for box, generated_path in repairs:
    x0, y0, x1, y1 = box
    size = (x1 - x0, y1 - y0)
    generated = Image.open(generated_path).convert("RGB").resize(size, Image.Resampling.LANCZOS)
    original = base.crop(box)
    mask = mask_full.crop(box).filter(ImageFilter.GaussianBlur(1.2))
    base.paste(Image.composite(generated, original, mask), (x0, y0))

destination = out / "demiurge_highlighted_anatomy_repaired_master.png"
base.save(destination)
print(destination)
print(base.size)
