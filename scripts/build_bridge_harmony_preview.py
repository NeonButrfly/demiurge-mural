"""Build a current artwork depth preview and a 100 mm printable sample."""

import argparse
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
CROPS_SOURCE_PX = {
    "trio": (1120, 1200, 1376, 1456),
    "kharn": (1536, 1536, 1792, 1792),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    source = args.source if args.source.is_absolute() else ROOT / args.source
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("L")
    if image.size != (2048, 2048):
        raise ValueError(image.size)
    gray = np.asarray(image.resize((1025, 1025), Image.Resampling.LANCZOS), dtype=np.float32)
    height = BASE_MM + np.power(gray / 255.0, GAMMA) * EMBOSS_MM
    Image.fromarray(np.round(height / (BASE_MM + EMBOSS_MM) * 65535).astype("uint16")).save(output_dir / "bridge_heightmap_16bit.png")

    # Render surface normals under upper-left raking light for a quick relief read.
    pitch = SIZE_MM / 1024
    dy, dx = np.gradient(height, pitch)
    normals = np.stack((-dx, -dy, np.ones_like(dx)), axis=2)
    normals /= np.linalg.norm(normals, axis=2, keepdims=True)
    light = np.array([-0.65, -0.55, 0.52], dtype=np.float32)
    light /= np.linalg.norm(light)
    shade = np.clip(0.2 + 0.8 * np.maximum(np.sum(normals * light, axis=2), 0), 0, 1)
    Image.fromarray(np.uint8(shade * 255)).save(output_dir / "bridge_raking_light.png")

    relief.PANEL_MM = 100.0
    relief.BASE_MM = BASE_MM
    relief.RELIEF_MM = EMBOSS_MM
    samples = {}
    for name, (x0, y0, x1, y1) in CROPS_SOURCE_PX.items():
        crop = height[y0 // 2:y1 // 2 + 1, x0 // 2:x1 // 2 + 1]
        if crop.shape != (129, 129):
            raise ValueError(crop.shape)
        triangles = relief.triangles_for_panel(crop)
        stl = output_dir / f"bridge_{name}_100mm_sample.stl"
        relief.write_binary_stl(stl, triangles, f"{name} sample")
        samples[name] = {
            "crop_source_px": [x0, y0, x1, y1],
            "file": str(stl.relative_to(ROOT)),
            "size_mm": [100.0, 100.0],
            "vertices_per_axis": 129,
            "triangle_count": int(len(triangles)),
            "z_range_mm": [float(triangles[:, :, 2].min()), float(triangles[:, :, 2].max())],
        }
    manifest = {
        "source": str(source.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "full_size_mm": [SIZE_MM, SIZE_MM],
        "base_mm": BASE_MM,
        "emboss_above_base_mm": EMBOSS_MM,
        "total_max_mm": BASE_MM + EMBOSS_MM,
        "height_gamma": GAMMA,
        "samples": samples,
        "physical_print_tested": False,
    }
    (output_dir / "bridge_relief_preview.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
