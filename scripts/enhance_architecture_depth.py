from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "single" / "demiurge_single_800mm_grayscale.png"
OUTPUT = ROOT / "outputs" / "single" / "demiurge_single_800mm_architecture_depth_enhanced_grayscale.png"

LOW_Z = 16
BORDER_PX = 13


def main() -> None:
    image = Image.open(SOURCE).convert("L")
    if image.size != (2048, 2048):
        raise ValueError(f"Expected 2048x2048 source, got {image.size}")

    interior = image.crop((BORDER_PX, BORDER_PX, 2048 - BORDER_PX, 2048 - BORDER_PX))
    pixels = np.asarray(interior, dtype=np.float32)

    # Weight the outer architectural zones most strongly and feather into the
    # central relief so the main figures are not flattened or reinterpreted.
    width = pixels.shape[1]
    x = np.arange(width, dtype=np.float32) / (width - 1)
    left = np.clip((0.44 - x) / 0.12, 0.0, 1.0)
    right = np.clip((x - 0.56) / 0.12, 0.0, 1.0)
    side_weight = np.maximum(left, right)
    side_weight = side_weight[None, :]

    # Contrast expansion separates darker recesses from brighter architectural
    # planes. Unsharp masking restores fine tower, arch, window, and circle edges.
    contrast = np.clip((pixels - 128.0) * 1.28 + 128.0, 0.0, 255.0)
    sharpened = np.asarray(
        interior.filter(ImageFilter.UnsharpMask(radius=4, percent=170, threshold=3)),
        dtype=np.float32,
    )
    enhanced = np.clip(contrast * 0.68 + sharpened * 0.32, 0.0, 255.0)
    blend = side_weight * 0.82
    result_interior = np.rint(pixels * (1.0 - blend) + enhanced * blend).astype(np.uint8)

    result = Image.new("L", image.size, LOW_Z)
    result.paste(Image.fromarray(result_interior, mode="L"), (BORDER_PX, BORDER_PX))
    result.save(OUTPUT, format="PNG", dpi=(2.56 * 25.4, 2.56 * 25.4))

    assert result.mode == "L" and result.size == (2048, 2048)
    assert all(value == LOW_Z for value in result.crop((0, 0, 2048, BORDER_PX)).getdata())
    assert all(value == LOW_Z for value in result.crop((0, 2048 - BORDER_PX, 2048, 2048)).getdata())
    assert all(value == LOW_Z for value in result.crop((0, 0, BORDER_PX, 2048)).getdata())
    assert all(value == LOW_Z for value in result.crop((2048 - BORDER_PX, 0, 2048, 2048)).getdata())


if __name__ == "__main__":
    main()
