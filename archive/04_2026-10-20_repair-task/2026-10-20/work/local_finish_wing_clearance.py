from pathlib import Path
from random import Random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


SOURCE = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_outpaint_clearance_raw_2488.webp")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_local_wing_clearance_2048.png")

TOP = 180
SIDE = 90


def add_stars(im: Image.Image) -> None:
    draw = ImageDraw.Draw(im)
    rng = Random(4815162342)
    for _ in range(165):
        x = rng.randrange(120, im.width - 80)
        y = rng.randrange(10, TOP - 10)
        r = rng.choices([1, 2, 3], [86, 12, 2])[0]
        v = rng.randrange(125, 230)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=v)


def main() -> None:
    src = Image.open(SOURCE).convert("L")
    w, h = src.size
    size = w + 2 * SIDE

    # A subdued full-bleed continuation under the preserved mural prevents a
    # flat border while keeping the narrow added sides visually quiet.
    under = src.resize((size, size), Image.Resampling.LANCZOS)
    under = under.filter(ImageFilter.GaussianBlur(18))
    under = ImageEnhance.Brightness(under).enhance(0.34)
    canvas = under.copy()

    # Replace the upper addition with neutral black relief sky and sparse stars.
    sky = Image.new("L", (size, TOP + 20), 7)
    sky = sky.filter(ImageFilter.GaussianBlur(2))
    add_stars(sky)
    canvas.paste(sky, (0, 0))

    # Continue only the remaining clipped feather group. Reflecting its own
    # edge texture guarantees a clean join; a tapered mask makes it terminate
    # inside the new sky rather than at the outer canvas edge.
    strip = src.crop((0, 0, w, TOP)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    wing_shape = Image.new("L", (w, TOP), 0)
    d = ImageDraw.Draw(wing_shape)
    d.polygon([(1450, TOP), (1580, 98), (1695, 48), (1815, 32),
               (1995, 76), (2110, TOP)], fill=255)
    lum = np.asarray(strip, dtype=np.float32)
    detail = np.clip((lum - 28.0) * 4.2, 0, 255)
    shape = np.asarray(wing_shape, dtype=np.float32)
    fade = np.clip((np.arange(TOP, dtype=np.float32) - 42) / 78.0, 0, 1)[:, None]
    mask = np.minimum(shape, detail) * fade
    mask_im = Image.fromarray(np.clip(mask, 0, 255).astype(np.uint8), "L")
    mask_im = mask_im.filter(ImageFilter.GaussianBlur(1.4))
    canvas.paste(strip, (SIDE, 0), mask_im)

    # The source is placed unchanged below the added sky. A tiny vertical blend
    # in dark pixels removes any straight join without softening the figures.
    canvas.paste(src, (SIDE, TOP))
    arr = np.asarray(canvas, dtype=np.float32)
    src_arr = np.asarray(src, dtype=np.float32)
    for i in range(14):
        y = TOP + i
        a = (i + 1) / 14.0
        dark = np.clip((85.0 - src_arr[i]) / 85.0, 0, 1)
        bg = arr[TOP - 1, SIDE:SIDE+w]
        arr[y, SIDE:SIDE+w] = src_arr[i] * (1 - dark * (1-a) * 0.28) + bg * dark * (1-a) * 0.28

    final = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
    final = final.resize((2048, 2048), Image.Resampling.LANCZOS).convert("RGB")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUTPUT, "PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print(f"working_canvas={size}x{size}; final=2048x2048")


if __name__ == "__main__":
    main()
