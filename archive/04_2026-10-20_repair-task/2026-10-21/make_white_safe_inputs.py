from pathlib import Path
from PIL import Image, ImageDraw

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs")
jobs = {
    "white_a_midleft": [(90, 170, 360, 385)],
    "white_c_lowercenter": [(185, 45, 475, 355), (400, 330, 650, 625)],
    "white_d_lowerright": [(0, 0, 190, 270), (300, 285, 650, 675)],
}

for stem, boxes in jobs.items():
    for suffix in ("clean", "annotated"):
        image = Image.open(root / f"{stem}_{suffix}.png").convert("RGB")
        draw = ImageDraw.Draw(image)
        for box in boxes:
            draw.rounded_rectangle(box, radius=18, fill=(20, 13, 21))
        image.save(root / f"{stem}_{suffix}_safe.png")
