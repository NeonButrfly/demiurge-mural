from pathlib import Path
from random import Random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


SOURCE = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\ChatGPT Image Oct 20, 2026, 05_35_27 AM.png")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_mural_full_bleed_local_2048.png")

TOP = 132
SIDE = 66


def make_top_background(src: Image.Image) -> Image.Image:
    w, _ = src.size
    edge = src.crop((0, 0, w, 46)).resize((w, TOP), Image.Resampling.BICUBIC)
    edge = edge.filter(ImageFilter.GaussianBlur(10))
    arr = np.asarray(edge, dtype=np.float32)
    yy, xx = np.mgrid[0:TOP, 0:w]
    # Quiet relief background. The right side is darker night sky.
    vertical = 0.52 + 0.38 * (yy / max(1, TOP - 1))
    right_sky = 1.0 - 0.24 * np.clip((xx - 800) / 331, 0, 1)
    arr *= vertical * right_sky
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")


def add_starfield(top: Image.Image) -> None:
    draw = ImageDraw.Draw(top)
    rng = Random(20102026)
    for _ in range(92):
        x = rng.randrange(845, top.width - 8)
        y = rng.randrange(8, TOP - 8)
        r = rng.choices([1, 2], [88, 12])[0]
        value = rng.randrange(145, 235)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=value)


def wing_continuation(src: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Reflect only feather texture, then fade it to pointed ends before the edge."""
    w, _ = src.size
    reflected = src.crop((0, 0, w, TOP)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    # The two feathered angel-wing groups that meet the source's top edge.
    shape = Image.new("L", (w, TOP), 0)
    d = ImageDraw.Draw(shape)
    d.polygon([(34, TOP), (55, 42), (120, 12), (360, 6), (423, TOP)], fill=255)
    d.polygon([(455, TOP), (482, 37), (555, 7), (765, 8), (806, TOP)], fill=255)

    # Use local brightness to retain feather ridges, while excluding dark gaps.
    lum = np.asarray(reflected, dtype=np.float32)
    detail = np.clip((lum - 45.0) * 3.2, 0, 255).astype(np.uint8)
    mask = np.minimum(np.asarray(shape), detail).astype(np.uint8)

    # Feather tips end inside the canvas. Nothing remains clipped at y=0.
    fade = np.clip((np.arange(TOP, dtype=np.float32) - 10) / 38.0, 0, 1)[:, None]
    mask = (mask.astype(np.float32) * fade).astype(np.uint8)
    mask_img = Image.fromarray(mask, "L").filter(ImageFilter.GaussianBlur(1.1))
    return reflected, mask_img


def main() -> None:
    src = Image.open(SOURCE).convert("L")
    w, h = src.size
    canvas = Image.new("L", (w + 2 * SIDE, h + TOP), 0)

    top = make_top_background(src)
    add_starfield(top)
    wing, wing_mask = wing_continuation(src)
    top.paste(wing, (0, 0), wing_mask)
    canvas.paste(top, (SIDE, 0))
    canvas.paste(src, (SIDE, TOP))

    # Narrow full-height side continuations. These fill the canvas edge to edge
    # and read as adjacent architecture rather than a flat picture border.
    assembled = canvas.crop((SIDE, 0, SIDE + w, h + TOP))
    left = assembled.crop((0, 0, SIDE, h + TOP)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    right = assembled.crop((w - SIDE, 0, w, h + TOP)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    canvas.paste(left, (0, 0))
    canvas.paste(right, (SIDE + w, 0))

    final = canvas.resize((2048, 2048), Image.Resampling.LANCZOS).convert("RGB")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUTPUT, "PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print(f"full_bleed={canvas.size[0]}x{canvas.size[1]} -> 2048x2048")


if __name__ == "__main__":
    main()
