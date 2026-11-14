"""Build a current artwork depth preview and a 100 mm printable sample."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

import generate_bas_relief as relief


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "bridge_harmony"
SOURCE = OUT / "demiurge_bridge_harmonized.png"
BASE_MM = 3.0
EMBOSS_MM = 12.0
GAMMA = 0.85
SIZE_MM = 800.0
CROP_SOURCE_PX = (1120, 1200, 1376, 1456)


def main() -> None:
    image = Image.open(SOURCE).convert("L")
    if image.size != (2048, 2048):
        raise ValueError(image.size)
    gray = np.asarray(image.resize((1025, 1025), Image.Resampling.LANCZOS), dtype=np.float32)
    height = BASE_MM + np.power(gray / 255.0, GAMMA) * EMBOSS_MM
    Image.fromarray(np.round(height / (BASE_MM + EMBOSS_MM) * 65535).astype("uint16")).save(OUT / "bridge_harmony_heightmap_16bit.png")

    # Render surface normals under upper-left raking light for a quick relief read.
    pitch = SIZE_MM / 1024
    dy, dx = np.gradient(height, pitch)
    normals = np.stack((-dx, -dy, np.ones_like(dx)), axis=2)
    normals /= np.linalg.norm(normals, axis=2, keepdims=True)
    light = np.array([-0.65, -0.55, 0.52], dtype=np.float32)
    light /= np.linalg.norm(light)
    shade = np.clip(0.2 + 0.8 * np.maximum(np.sum(normals * light, axis=2), 0), 0, 1)
    Image.fromarray(np.uint8(shade * 255)).save(OUT / "bridge_harmony_raking_light.png")

    x0, y0, x1, y1 = CROP_SOURCE_PX
    crop = height[y0 // 2:y1 // 2 + 1, x0 // 2:x1 // 2 + 1]
    if crop.shape != (129, 129):
        raise ValueError(crop.shape)
    relief.PANEL_MM = 100.0
    relief.BASE_MM = BASE_MM
    relief.RELIEF_MM = EMBOSS_MM
    triangles = relief.triangles_for_panel(crop)
    stl = OUT / "bridge_harmony_trio_100mm_sample.stl"
    relief.write_binary_stl(stl, triangles, "trio seam sample")

    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "full_size_mm": [SIZE_MM, SIZE_MM],
        "base_mm": BASE_MM,
        "emboss_above_base_mm": EMBOSS_MM,
        "total_max_mm": BASE_MM + EMBOSS_MM,
        "height_gamma": GAMMA,
        "crop_source_px": list(CROP_SOURCE_PX),
        "crop_size_mm": [100.0, 100.0],
        "crop_vertices_per_axis": 129,
        "crop_triangle_count": int(len(triangles)),
        "crop_z_range_mm": [float(triangles[:, :, 2].min()), float(triangles[:, :, 2].max())],
        "physical_print_tested": False,
    }
    (OUT / "bridge_harmony_relief_preview.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
