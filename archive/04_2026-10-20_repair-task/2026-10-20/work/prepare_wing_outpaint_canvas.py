from pathlib import Path
from PIL import Image

SOURCE = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\ChatGPT Image Oct 20, 2026, 05_35_27 AM.png")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\work\demiurge_wing_outpaint_input.png")

# Add enough room above for complete feather tips. Equal total horizontal
# expansion keeps the working canvas square without cropping the mural.
TOP = 220
SIDE = 110

src = Image.open(SOURCE).convert("RGBA")
w, h = src.size
canvas = Image.new("RGBA", (w + 2 * SIDE, h + TOP), (0, 0, 0, 0))
canvas.alpha_composite(src, (SIDE, TOP))
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUTPUT, "PNG", optimize=True)
print(f"saved={OUTPUT}")
print(f"canvas={canvas.width}x{canvas.height}, source_offset=({SIDE},{TOP})")
