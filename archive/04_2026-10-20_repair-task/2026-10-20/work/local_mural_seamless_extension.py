from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


SOURCE = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\ChatGPT Image Oct 20, 2026, 05_35_27 AM.png")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_mural_seamless_local_edit_2048.png")

# Work at the source scale first. The extension is part of the picture rather
# than a decorative frame; the finished mural is resized only once at the end.
EXTEND_TOP = 132
EXTEND_RIGHT = 132


def feather_extension(src: Image.Image) -> Image.Image:
    """Continue the top edge upward with an edge-matched, tapered reflection."""
    w, _ = src.size
    strip = src.crop((0, 0, w, EXTEND_TOP + 38))
    strip = strip.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    # Taper the reflected texture toward the new outer edge. This breaks the
    # obvious mirror appearance while retaining the wing ridges at the join.
    arr = np.asarray(strip, dtype=np.float32)
    y = np.linspace(0.0, 1.0, arr.shape[0], dtype=np.float32)[:, None]
    smooth = np.asarray(strip.filter(ImageFilter.GaussianBlur(5.0)), dtype=np.float32)
    arr = arr * (0.42 + 0.58 * y) + smooth * (0.58 - 0.58 * y)

    # Keep the added upper-right region dark enough to read as night sky while
    # leaving the bright feather extensions on the left and center intact.
    x = np.linspace(0.0, 1.0, arr.shape[1], dtype=np.float32)[None, :]
    darken = 1.0 - 0.22 * np.clip((x - 0.72) / 0.28, 0.0, 1.0) * (1.0 - y)
    arr *= darken
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L").crop(
        (0, arr.shape[0] - EXTEND_TOP, w, arr.shape[0])
    )


def right_extension(src: Image.Image, height: int) -> Image.Image:
    """Continue sky and architecture to the right without a straight gutter."""
    w, h = src.size
    strip = src.crop((w - EXTEND_RIGHT - 44, 0, w, h))
    strip = strip.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    strip = strip.resize((EXTEND_RIGHT, height), Image.Resampling.LANCZOS)

    # A light horizontal blur softens repeated edge details without erasing the
    # Gothic relief texture.
    soft = strip.filter(ImageFilter.GaussianBlur(2.2))
    arr = np.asarray(strip, dtype=np.float32)
    soft_arr = np.asarray(soft, dtype=np.float32)
    x = np.linspace(0.0, 1.0, EXTEND_RIGHT, dtype=np.float32)[None, :]
    arr = arr * (1.0 - 0.36 * x) + soft_arr * (0.36 * x)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="L")


def main() -> None:
    source = Image.open(SOURCE).convert("L")
    w, h = source.size
    expanded = Image.new("L", (w + EXTEND_RIGHT, h + EXTEND_TOP), 0)

    top = feather_extension(source)
    expanded.paste(top, (0, 0))
    expanded.paste(source, (0, EXTEND_TOP))

    # Build the right continuation from the already assembled image so the
    # upper corner and the architecture meet without a rectangular border.
    right = right_extension(expanded.crop((0, 0, w, h + EXTEND_TOP)), h + EXTEND_TOP)
    expanded.paste(right, (w, 0))

    # Neutral grayscale and one high-quality resize to the requested size.
    expanded = ImageEnhance.Contrast(expanded).enhance(1.015)
    final = expanded.resize((2048, 2048), Image.Resampling.LANCZOS).convert("RGB")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUTPUT, format="PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print(f"source={w}x{h}")
    print(f"expanded={expanded.size[0]}x{expanded.size[1]}")
    print(f"final={final.size[0]}x{final.size[1]}")


if __name__ == "__main__":
    main()
