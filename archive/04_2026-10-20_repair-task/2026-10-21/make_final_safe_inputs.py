from pathlib import Path
from PIL import Image

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs")
names = ["fix_yellow_center", "fix_yellow_small", "fix_yellow_winged", "fix_yellow_lowerright"]

for name in names:
    mask = Image.open(root / f"{name}_mask.png").convert("L")
    dark = Image.new("RGB", mask.size, (20, 13, 21))
    for suffix in ("clean", "annotated"):
        image = Image.open(root / f"{name}_{suffix}.png").convert("RGB")
        Image.composite(dark, image, mask).save(root / f"{name}_{suffix}_safe.png")
