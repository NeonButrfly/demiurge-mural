from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "single" / "demiurge_single_800mm_architecture_depth_enhanced_grayscale.png"
DEPTH_MAP = ROOT / "assets" / "references" / "depthcarve-depth-map-8bit_1.png"
OUTPUT = ROOT / "outputs" / "single" / "demiurge_single_800mm_depthcarve_blended_grayscale.png"

LOW_Z = 16
BORDER_PX = 13


def main() -> None:
    base_image = Image.open(SOURCE).convert("L")
    depth_image = Image.open(DEPTH_MAP).convert("L")
    if base_image.size != (2048, 2048):
        raise ValueError(f"Expected 2048x2048 base image, got {base_image.size}")

    interior_box = (BORDER_PX, BORDER_PX, 2048 - BORDER_PX, 2048 - BORDER_PX)
    base_interior = np.asarray(base_image.crop(interior_box), dtype=np.float32)
    depth = np.asarray(depth_image.resize(base_interior.shape[::-1], Image.Resampling.LANCZOS), dtype=np.float32)

    # Convert the supplied map into a restrained, centered low-frequency field.
    # This adds broad relief variation without replacing the artwork detail.
    centered = (depth - float(depth.mean())) / max(float(depth.std()), 1.0)
    depth_delta = np.clip(centered, -2.0, 2.0) * 12.0

    width = base_interior.shape[1]
    x = np.arange(width, dtype=np.float32) / (width - 1)
    left = np.clip((0.44 - x) / 0.12, 0.0, 1.0)
    right = np.clip((x - 0.56) / 0.12, 0.0, 1.0)
    side_weight = np.maximum(left, right)[None, :]
    result_interior = np.clip(base_interior + depth_delta * side_weight * 0.85, 0.0, 255.0).astype(np.uint8)

    result = Image.new("L", base_image.size, LOW_Z)
    result.paste(Image.fromarray(result_interior, mode="L"), (BORDER_PX, BORDER_PX))
    result.save(OUTPUT, format="PNG", dpi=(2.56 * 25.4, 2.56 * 25.4))

    assert result.mode == "L" and result.size == (2048, 2048)
    assert all(value == LOW_Z for value in result.crop((0, 0, 2048, BORDER_PX)).getdata())
    assert all(value == LOW_Z for value in result.crop((0, 2048 - BORDER_PX, 2048, 2048)).getdata())
    assert all(value == LOW_Z for value in result.crop((0, 0, BORDER_PX, 2048)).getdata())
    assert all(value == LOW_Z for value in result.crop((2048 - BORDER_PX, 0, 2048, 2048)).getdata())


if __name__ == "__main__":
    main()
