from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from generate_bas_relief import generate


ROOT = Path(__file__).resolve().parents[1]
ENHANCED = ROOT / "outputs" / "single" / "demiurge_single_800mm_architecture_depth_enhanced_grayscale.png"
BASELINE = ROOT / "outputs" / "single" / "demiurge_single_800mm_grayscale.png"
OUTPUT = ROOT / "outputs" / "single" / "demiurge_single_800mm_circular_regions_restored_grayscale.png"
RELIEF_OUTPUT = ROOT / "outputs" / "relief_restored"
MASK_OUTPUT = ROOT / "outputs" / "single" / "demiurge_circular_regions_restoration_mask.png"

SIZE = (2048, 2048)
BORDER_PX = 13


def feathered_region_mask() -> Image.Image:
    mask = Image.new("L", SIZE, 0)
    draw = ImageDraw.Draw(mask)
    # Restore each circle plus the immediately surrounding towers, arches,
    # windows, and sky. Feathering avoids a visible transition into the
    # unchanged enhanced artwork.
    draw.rectangle((0, 70, 560, 680), fill=255)
    draw.ellipse((80, 95, 570, 605), fill=255)
    draw.rectangle((1490, 45, 2047, 630), fill=255)
    draw.ellipse((1540, 35, 2040, 545), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=42))

    # Never alter the existing low-Z perimeter.
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0, 0, 2047, BORDER_PX - 1), fill=0)
    draw.rectangle((0, 2048 - BORDER_PX, 2047, 2047), fill=0)
    draw.rectangle((0, 0, BORDER_PX - 1, 2047), fill=0)
    draw.rectangle((2048 - BORDER_PX, 0, 2047, 2047), fill=0)
    return mask


def main() -> None:
    enhanced = Image.open(ENHANCED).convert("L")
    baseline = Image.open(BASELINE).convert("L")
    if enhanced.size != SIZE or baseline.size != SIZE:
        raise ValueError("Both grayscale sources must be exactly 2048x2048")

    mask = feathered_region_mask()
    patched = Image.composite(baseline, enhanced, mask)
    patched.save(OUTPUT, format="PNG", dpi=(2.56 * 25.4, 2.56 * 25.4))
    mask.save(MASK_OUTPUT, format="PNG")

    assert patched.mode == "L" and patched.size == SIZE
    assert all(value == 16 for value in patched.crop((0, 0, 2048, BORDER_PX)).getdata())
    assert all(value == 16 for value in patched.crop((0, 2048 - BORDER_PX, 2048, 2048)).getdata())
    assert all(value == 16 for value in patched.crop((0, 0, BORDER_PX, 2048)).getdata())
    assert all(value == 16 for value in patched.crop((2048 - BORDER_PX, 0, 2048, 2048)).getdata())

    generate(
        source=OUTPUT,
        output_dir=RELIEF_OUTPUT,
        file_prefix="demiurge_restored_bas_relief_panel_",
    )
    manifest_path = RELIEF_OUTPUT / "relief_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["restoration"] = {
        "baseline": str(BASELINE.relative_to(ROOT)),
        "enhanced_input": str(ENHANCED.relative_to(ROOT)),
        "mask": str(MASK_OUTPUT.relative_to(ROOT)),
        "scope": "upper-left star circle and surrounding architecture; upper-right eclipse circle and surrounding architecture",
        "border_preserved_px": BORDER_PX,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
