from pathlib import Path
from random import Random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


SOURCE = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\ChatGPT Image Oct 20, 2026, 05_35_27 AM.png")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_mural_local_preservation_edit_2048.png")

CANVAS = 2048
MARGIN = 112  # 5.47% of the final canvas
INNER = CANVAS - MARGIN


def make_edge_background(source: Image.Image) -> Image.Image:
    """Create a quiet continuation behind the preserved source without inventing figures."""
    large = source.resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    large = large.filter(ImageFilter.GaussianBlur(24))
    large = ImageEnhance.Brightness(large).enhance(0.25)
    large = ImageEnhance.Contrast(large).enhance(0.75)
    return large.convert("L")


def add_stars(canvas: Image.Image) -> None:
    """Add deterministic neutral-gray stars only in the new top/right sky gutters."""
    draw = ImageDraw.Draw(canvas)
    rng = Random(20261020)

    # Top gutter, weighted toward the upper-right night-sky region.
    for _ in range(245):
        x = rng.randrange(18, CANVAS - 18)
        y = rng.randrange(8, MARGIN - 8)
        if x < 760 and rng.random() < 0.72:
            continue
        radius = rng.choices([1, 2, 3], weights=[82, 16, 2])[0]
        value = rng.randrange(145, 236)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=value)

    # Right gutter, leaving the lower architectural edge visually quiet.
    for _ in range(220):
        x = rng.randrange(CANVAS - MARGIN + 10, CANVAS - 8)
        y = rng.randrange(8, 1040)
        radius = rng.choices([1, 2, 3], weights=[84, 14, 2])[0]
        value = rng.randrange(140, 230)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=value)


def main() -> None:
    source = Image.open(SOURCE).convert("L")
    preserved = source.resize((INNER, INNER), Image.Resampling.LANCZOS)

    canvas = make_edge_background(source)

    # Darken the new top/right space into a continuous night sky.
    arr = np.asarray(canvas, dtype=np.float32)
    yy, xx = np.mgrid[0:CANVAS, 0:CANVAS]
    top_weight = np.clip((MARGIN - yy) / MARGIN, 0, 1)
    right_weight = np.clip((xx - (CANVAS - MARGIN)) / MARGIN, 0, 1)
    sky_weight = np.maximum(top_weight, right_weight)
    arr = arr * (1.0 - 0.68 * sky_weight)
    canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L")

    add_stars(canvas)

    # Add space only above and to the right. The complete original lower and
    # left composition still reaches the final canvas edges.
    canvas.paste(preserved, (0, MARGIN))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(OUTPUT, format="PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print(f"size={canvas.size[0]}x{canvas.size[1]}")
    print(f"inset={MARGIN}px ({MARGIN / CANVAS:.2%})")


if __name__ == "__main__":
    main()
