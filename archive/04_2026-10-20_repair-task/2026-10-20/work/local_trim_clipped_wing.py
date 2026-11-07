from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


SOURCE = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_outpaint_clearance_raw_2488.webp")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_local_contained_wings_2048.png")


def main() -> None:
    im = Image.open(SOURCE).convert("L")
    arr = np.asarray(im, dtype=np.float32).copy()
    h, w = arr.shape

    # The only remaining clipped feather group occupies this top-right span.
    # Replace the area above a shallow U-shaped contour with nearby starfield,
    # leaving a centered feather tip and clear sky above it.
    mask = np.zeros((h, w), dtype=np.uint8)
    x0, x1, center = 1510, 2110, 1810
    for x in range(x0, x1):
        boundary = int(48 + 0.00225 * (x - center) ** 2)
        boundary = min(boundary, 210)
        mask[:boundary, x] = 255

    # Use clean night sky from the far-right top of the same mural. Repeating a
    # small offset preserves the source's grain and star brightness.
    donor = arr.copy()
    for x in range(x0, x1):
        sx = min(w - 1, x + 330)
        donor[:, x] = arr[:, sx]

    soft = np.asarray(Image.fromarray(mask, "L").filter(ImageFilter.GaussianBlur(2.4)), dtype=np.float32) / 255.0
    arr = arr * (1.0 - soft) + donor * soft

    fixed = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")
    fixed = fixed.resize((2048, 2048), Image.Resampling.LANCZOS).convert("RGB")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fixed.save(OUTPUT, "PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print("local sky-composite applied; final=2048x2048")


if __name__ == "__main__":
    main()
