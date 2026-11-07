from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


BASE = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_zoomout_mericanii_relief_2048.png")
ORIGINAL = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\ChatGPT Image Oct 20, 2026, 05_35_27 AM.png")
REFERENCE = Path(r"C:\Users\Keifm\OneDrive\Desktop\demiurge\demiurge_full_four_panel_source_2048x2048.png")
OUTPUT = Path(r"C:\Users\Keifm\Documents\Codex\2026-10-20\referenced-chatgpt-conversation-this-is-an\outputs\demiurge_repaired_from_last_good_2048.png")


def smoothstep(v):
    v = np.clip(v, 0.0, 1.0)
    return v * v * (3.0 - 2.0 * v)


def main():
    base = Image.open(BASE).convert("L")
    orig = Image.open(ORIGINAL).convert("L")
    W = H = 2048

    # The 15% zoom-out places the original mural in the central 85% square.
    inner = round(W * 0.85)
    ox = (W - inner) // 2
    oy = ox
    orig_scaled = orig.resize((inner, inner), Image.Resampling.LANCZOS)
    orig_layer = Image.new("L", (W, H), 0)
    orig_layer.paste(orig_scaled, (ox, oy))

    base_a = np.asarray(base, dtype=np.float32)
    orig_a = np.asarray(orig_layer, dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]

    # Restore only the lower original mural. Wide feathering on all four sides
    # prevents the rectangular joins created by the rejected first composite.
    bottom = smoothstep((yy - 930.0) / 330.0)
    left_fade = smoothstep((xx - ox) / 150.0)
    right_fade = smoothstep((ox + inner - xx) / 150.0)
    lower_limit = smoothstep((oy + inner - yy) / 150.0)
    restore = bottom * left_fade * right_fade * lower_limit
    merged = base_a * (1.0 - restore) + orig_a * restore

    final = Image.fromarray(np.clip(merged, 0, 255).astype(np.uint8), "L").convert("RGB")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUTPUT, "PNG", optimize=True)
    print(f"saved={OUTPUT}")
    print(f"original_mapping={inner}px at ({ox},{oy}); final=2048x2048 grayscale")


if __name__ == "__main__":
    main()
