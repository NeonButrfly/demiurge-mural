from pathlib import Path
from math import cos, pi, sin

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


SOURCE = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_zoomout_pyramids_raw_2048.webp")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_zoomout_mericanii_relief_2048.png")


def relief_line(draw: ImageDraw.ImageDraw, points, width=3, value=72):
    # Dark recess beside a light ridge gives the line a shallow carved profile.
    shadow = [(x + 2, y + 2) for x, y in points]
    draw.line(shadow, fill=8, width=width + 2, joint="curve")
    draw.line(points, fill=value, width=width, joint="curve")


def pyramid(draw: ImageDraw.ImageDraw, cx, base_y, half_w, peak_y):
    left, right = cx - half_w, cx + half_w
    relief_line(draw, [(left, base_y), (cx, peak_y), (right, base_y)], 4, 68)
    relief_line(draw, [(left, base_y), (right, base_y)], 3, 58)
    relief_line(draw, [(cx, peak_y), (cx, base_y)], 2, 47)
    for frac in (0.24, 0.43, 0.61, 0.77):
        y = int(peak_y + (base_y - peak_y) * frac)
        span = int(half_w * frac)
        relief_line(draw, [(cx - span, y), (cx + span, y)], 2, 43 + int(frac * 22))
    # Machine-divine panel channels.
    for frac in (-0.62, -0.31, 0.31, 0.62):
        bx = int(cx + half_w * frac)
        relief_line(draw, [(cx, peak_y + 8), (bx, base_y - 3)], 1, 38)


def empire_medallion(draw: ImageDraw.ImageDraw, cx, cy, r):
    # Recess and double raised rim.
    draw.ellipse((cx-r-5, cy-r-5, cx+r+5, cy+r+5), outline=7, width=8)
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=86, width=4)
    draw.ellipse((cx-r+10, cy-r+10, cx+r-10, cy+r-10), outline=48, width=3)
    # Empire sunburst.
    for i in range(24):
        a = 2*pi*i/24
        inner = r + 8
        outer = r + (34 if i % 2 == 0 else 24)
        relief_line(draw, [
            (int(cx + inner*cos(a)), int(cy + inner*sin(a))),
            (int(cx + outer*cos(a)), int(cy + outer*sin(a)))
        ], 2, 63)
    # Earth sphere, equator, meridian, and simplified continents.
    er = int(r * 0.58)
    draw.ellipse((cx-er, cy-er, cx+er, cy+er), outline=78, width=3)
    draw.arc((cx-er, cy-int(er*.38), cx+er, cy+int(er*.38)), 0, 360, fill=49, width=2)
    draw.arc((cx-int(er*.43), cy-er, cx+int(er*.43), cy+er), 90, 270, fill=50, width=2)
    draw.arc((cx-int(er*.43), cy-er, cx+int(er*.43), cy+er), 270, 90, fill=50, width=2)
    relief_line(draw, [(cx-30,cy-18),(cx-13,cy-30),(cx+2,cy-22),(cx+16,cy-6),
                       (cx+4,cy+8),(cx-8,cy+1),(cx-20,cy+18),(cx-35,cy+8)], 2, 66)


def main():
    src = Image.open(SOURCE).convert("L")
    arr = np.asarray(src, dtype=np.float32)

    # Remove isolated point stars from open upper sky. Long relief edges and
    # feather structures survive because their local median is not black.
    med = np.asarray(src.filter(ImageFilter.MedianFilter(5)), dtype=np.float32)
    med9 = np.asarray(src.filter(ImageFilter.MedianFilter(9)), dtype=np.float32)
    broad = np.asarray(src.filter(ImageFilter.GaussianBlur(8)), dtype=np.float32)
    yy, _ = np.mgrid[0:src.height, 0:src.width]
    isolated = (yy < 360) & (arr > 75) & (med < 23)
    cleaned = arr.copy()
    cleaned[isolated] = med[isolated]
    # Flatten the remaining point-star field only where the broad neighborhood
    # is truly empty sky. Bright, connected wings and architecture are retained.
    open_sky = (yy < 335) & (broad < 25)
    texture = 6.0 + np.asarray(src.filter(ImageFilter.GaussianBlur(24)), dtype=np.float32) * 0.10
    cleaned[open_sky] = texture[open_sky]
    # Clear dense remaining stars from the broad, empty outer sky while
    # protecting the wing and halo zones. The circular starfields sit below
    # this mask and remain unchanged.
    xx_grid = np.mgrid[0:src.height, 0:src.width][1]
    broad_open = (
        ((yy < 145) & (xx_grid > 155) & (xx_grid < 955)) |
        ((yy < 335) & (xx_grid > 1210))
    ) & (med9 < 34)
    cleaned[broad_open] = texture[broad_open]
    base = Image.fromarray(np.clip(cleaned, 0, 255).astype(np.uint8), "L")

    detail = Image.new("L", src.size, 0)
    d = ImageDraw.Draw(detail)
    pyramid(d, 650, 325, 205, 82)
    pyramid(d, 875, 330, 235, 48)
    pyramid(d, 1080, 323, 180, 108)
    empire_medallion(d, 1660, 175, 76)

    # Allow new ridges only over genuinely dark sky so wings, halo rays, portals,
    # and architecture remain in front of the added background relief.
    detail_arr = np.asarray(detail, dtype=np.float32)
    sky = np.clip((62.0 - cleaned) / 38.0, 0, 1)
    sky *= np.clip((390.0 - yy) / 115.0, 0, 1)
    # Keep the existing upper-right circular portal completely untouched.
    xx = xx_grid
    portal_guard = ((xx - 1305)**2 + (yy - 495)**2) < 165**2
    sky[portal_guard] = 0
    alpha = np.clip(detail_arr / 68.0, 0, 1) * sky
    raised = np.maximum(cleaned, detail_arr * 1.24)
    out = cleaned * (1-alpha) + raised * alpha

    final = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "L").convert("RGB")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUTPUT, "PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print("size=2048x2048; RGB channels identical")


if __name__ == "__main__":
    main()
