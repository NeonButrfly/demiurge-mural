from pathlib import Path
from PIL import Image

root = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an")
out = root / "outputs"
working = Image.open(out / "demiurge_newmasks_white_body_pass.png").convert("RGB")
annotation = Image.open(r"C:\Users\Keifm\OneDrive\Desktop\newmasks.png").convert("RGB")
green = Image.open(out / "newmask_green_precise.png").convert("L")
red = Image.open(out / "newmask_red_precise.png").convert("L")

regions = {
    "g1_shoulder": (600, 850, 850, 1080),
    "g2_center_body": (620, 1180, 1040, 1640),
    "g3_hand": (1050, 1030, 1320, 1330),
    "g4_bottom_faces": (150, 1820, 700, 2048),
    "g5_lower_right": (1350, 1500, 1900, 2048),
    "r1_upper_left": (250, 380, 850, 950),
    "r2_middle": (850, 1050, 1500, 1660),
    "r3_lower_left": (0, 1300, 850, 2048),
    "r4_lower_right": (1250, 1200, 2048, 2048),
    "r5_bottom_center": (450, 1600, 1150, 2048),
}

for name, box in regions.items():
    working.crop(box).save(out / f"{name}_clean.png")
    annotation.crop(box).save(out / f"{name}_annotated.png")
    (green if name.startswith("g") else red).crop(box).save(out / f"{name}_mask.png")
