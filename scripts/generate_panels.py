from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "source" / "demiurge_full_four_panel_source_2048x2048_grayscale.png"
PANEL_DIR = ROOT / "outputs" / "panels"
PREVIEW_DIR = ROOT / "outputs" / "previews"
SINGLE_DIR = ROOT / "outputs" / "single"

PIXELS_PER_MM = 2.56
PANEL_PX = 1024
BORDER_PX = round(5 * PIXELS_PER_MM)
INTERIOR_PX = PANEL_PX - 2 * BORDER_PX
LOW_Z = 16


def main() -> None:
    source = Image.open(SOURCE).convert("L")
    if source.size != (2048, 2048):
        raise ValueError(f"Expected 2048x2048 source, got {source.size}")

    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    SINGLE_DIR.mkdir(parents=True, exist_ok=True)

    single_size = PANEL_PX * 2
    single_interior_size = single_size - 2 * BORDER_PX
    single_interior = source.resize((single_interior_size, single_interior_size), Image.Resampling.LANCZOS)
    single = Image.new("L", (single_size, single_size), LOW_Z)
    single.paste(single_interior, (BORDER_PX, BORDER_PX))
    single.save(SINGLE_DIR / "demiurge_single_800mm_grayscale.png", format="PNG", dpi=(PIXELS_PER_MM * 25.4, PIXELS_PER_MM * 25.4))

    positions = {
        "01_upper_left": (0, 0),
        "02_upper_right": (1024, 0),
        "03_lower_left": (0, 1024),
        "04_lower_right": (1024, 1024),
    }
    panels = []
    for name, (left, top) in positions.items():
        quadrant = source.crop((left, top, left + 1024, top + 1024))
        interior = quadrant.resize((INTERIOR_PX, INTERIOR_PX), Image.Resampling.LANCZOS)
        panel = Image.new("L", (PANEL_PX, PANEL_PX), LOW_Z)
        panel.paste(interior, (BORDER_PX, BORDER_PX))
        output = PANEL_DIR / f"demiurge_panel_{name}_400mm_grayscale.png"
        panel.save(output, format="PNG", dpi=(PIXELS_PER_MM * 25.4, PIXELS_PER_MM * 25.4))
        panels.append(panel)

    combined = Image.new("L", (PANEL_PX * 2, PANEL_PX * 2), LOW_Z)
    for index, panel in enumerate(panels):
        combined.paste(panel, ((index % 2) * PANEL_PX, (index // 2) * PANEL_PX))
    combined.save(PREVIEW_DIR / "demiurge_four_panel_combined_preview.png", format="PNG")

    # Exact invariants checked here so the generator fails loudly if edited later.
    assert all(panel.mode == "L" and panel.size == (PANEL_PX, PANEL_PX) for panel in panels)
    for panel in panels:
        assert all(pixel == LOW_Z for pixel in list(panel.crop((0, 0, PANEL_PX, BORDER_PX)).getdata()))
        assert all(pixel == LOW_Z for pixel in list(panel.crop((0, PANEL_PX - BORDER_PX, PANEL_PX, PANEL_PX)).getdata()))
        assert all(pixel == LOW_Z for pixel in list(panel.crop((0, 0, BORDER_PX, PANEL_PX)).getdata()))
        assert all(pixel == LOW_Z for pixel in list(panel.crop((PANEL_PX - BORDER_PX, 0, PANEL_PX, PANEL_PX)).getdata()))
    assert single.mode == "L" and single.size == (PANEL_PX * 2, PANEL_PX * 2)
    assert all(pixel == LOW_Z for pixel in list(single.crop((0, 0, PANEL_PX * 2, BORDER_PX)).getdata()))
    assert all(pixel == LOW_Z for pixel in list(single.crop((0, PANEL_PX * 2 - BORDER_PX, PANEL_PX * 2, PANEL_PX * 2)).getdata()))
    assert all(pixel == LOW_Z for pixel in list(single.crop((0, 0, BORDER_PX, PANEL_PX * 2)).getdata()))
    assert all(pixel == LOW_Z for pixel in list(single.crop((PANEL_PX * 2 - BORDER_PX, 0, PANEL_PX * 2, PANEL_PX * 2)).getdata()))


if __name__ == "__main__":
    main()
