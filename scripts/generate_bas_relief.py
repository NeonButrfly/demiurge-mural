from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "single" / "demiurge_single_800mm_architecture_depth_enhanced_grayscale.png"
OUTPUT_DIR = ROOT / "outputs" / "relief"

PANEL_PX = 1024
GRID = 513  # Shared seam vertices: 512 intervals across each 400 mm panel.
PANEL_MM = 400.0
BASE_MM = 2.5
REFERENCE_MAX_Z_MM = 25.1175
RELIEF_MM = REFERENCE_MAX_Z_MM - BASE_MM
HEIGHT_GAMMA = 0.30
LOW_Z = 16
OUTER_BORDER_MM = 5.0


def triangles_for_panel(height: np.ndarray) -> np.ndarray:
    n = height.shape[0]
    axis = np.linspace(0.0, PANEL_MM, n, dtype=np.float32)
    xx, yy = np.meshgrid(axis, axis)
    top = np.stack((xx, yy, height), axis=-1)

    v00 = top[:-1, :-1]
    v10 = top[:-1, 1:]
    v01 = top[1:, :-1]
    v11 = top[1:, 1:]
    upper = np.stack((v00, v10, v11), axis=2)
    lower = np.stack((v00, v11, v01), axis=2)
    triangles = [upper.reshape(-1, 3, 3), lower.reshape(-1, 3, 3)]

    # Bottom plate uses the same grid so every subdivided wall edge has a
    # matching bottom-surface edge and the exported solid is closed.
    bottom_grid = np.stack((xx, yy, np.zeros_like(xx)), axis=-1)
    b00 = bottom_grid[:-1, :-1]
    b10 = bottom_grid[:-1, 1:]
    b01 = bottom_grid[1:, :-1]
    b11 = bottom_grid[1:, 1:]
    triangles.append(np.stack((b00, b11, b10), axis=2).reshape(-1, 3, 3))
    triangles.append(np.stack((b00, b01, b11), axis=2).reshape(-1, 3, 3))

    # Four perimeter walls close the solid.
    edges = [
        (top[0, :, :], np.array([0.0, 0.0, 0.0], dtype=np.float32), np.array([PANEL_MM, 0.0, 0.0], dtype=np.float32)),
        (top[-1, :, :], np.array([0.0, PANEL_MM, 0.0], dtype=np.float32), np.array([PANEL_MM, PANEL_MM, 0.0], dtype=np.float32)),
        (top[:, 0, :], np.array([0.0, 0.0, 0.0], dtype=np.float32), np.array([0.0, PANEL_MM, 0.0], dtype=np.float32)),
        (top[:, -1, :], np.array([PANEL_MM, 0.0, 0.0], dtype=np.float32), np.array([PANEL_MM, PANEL_MM, 0.0], dtype=np.float32)),
    ]
    for edge, bottom_start, bottom_end in edges:
        bottom_edge = np.linspace(bottom_start, bottom_end, n, dtype=np.float32)
        e0, e1 = edge[:-1], edge[1:]
        b0, b1 = bottom_edge[:-1], bottom_edge[1:]
        triangles.append(np.stack((e0, b0, b1), axis=1))
        triangles.append(np.stack((e0, b1, e1), axis=1))

    return np.concatenate(triangles, axis=0)


def write_binary_stl(path: Path, triangles: np.ndarray, name: str) -> None:
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths != 0)
    record = np.empty(
        triangles.shape[0],
        dtype=np.dtype([
            ("normal", "<f4", (3,)),
            ("v0", "<f4", (3,)),
            ("v1", "<f4", (3,)),
            ("v2", "<f4", (3,)),
            ("attribute", "<u2"),
        ]),
    )
    record["normal"] = normals
    record["v0"] = triangles[:, 0]
    record["v1"] = triangles[:, 1]
    record["v2"] = triangles[:, 2]
    record["attribute"] = 0
    header = (f"Demiurge Mural {name} | 400mm bas relief | base {BASE_MM}mm | relief {RELIEF_MM}mm").encode("ascii")[:80]
    header = header.ljust(80, b" ")
    with path.open("wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(record)))
        handle.write(record.tobytes())


def main() -> None:
    source = Image.open(SOURCE).convert("L")
    if source.size != (2048, 2048):
        raise ValueError(f"Expected 2048x2048 source, got {source.size}")
    shared_gray = np.asarray(source.resize((1025, 1025), Image.Resampling.LANCZOS), dtype=np.float32)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    panels = {
        "01_upper_left": (0, 0),
        "02_upper_right": (1024, 0),
        "03_lower_left": (0, 1024),
        "04_lower_right": (1024, 1024),
    }
    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "reference_example": "assets/references/panel_1_upper_left_example.stl",
        "panel_size_mm": [PANEL_MM, PANEL_MM],
        "overall_size_mm": [800.0, 800.0],
        "base_thickness_mm": BASE_MM,
        "maximum_relief_above_base_mm": RELIEF_MM,
        "maximum_total_height_mm": BASE_MM + RELIEF_MM,
        "reference_example_max_z_mm": REFERENCE_MAX_Z_MM,
        "height_gamma": HEIGHT_GAMMA,
        "outer_low_z_border_mm": OUTER_BORDER_MM,
        "grid_vertices_per_axis": GRID,
        "panels": {},
    }

    for name, (x0, y0) in panels.items():
        grid_x = 0 if x0 == 0 else 512
        grid_y = 0 if y0 == 0 else 512
        gray = shared_gray[grid_y:grid_y + GRID, grid_x:grid_x + GRID]
        normalized = np.clip(gray / 255.0, 0.0, 1.0)
        height = BASE_MM + np.power(normalized, HEIGHT_GAMMA) * RELIEF_MM

        # Only the outside edges of the complete 800 mm mural are forced to the
        # low-Z base. Internal panel seams remain continuous artwork surfaces.
        coords = np.linspace(0.0, PANEL_MM, GRID, dtype=np.float32)
        if x0 == 0:
            height[:, coords <= OUTER_BORDER_MM] = BASE_MM
        if x0 == 1024:
            height[:, coords >= PANEL_MM - OUTER_BORDER_MM] = BASE_MM
        if y0 == 0:
            height[coords <= OUTER_BORDER_MM, :] = BASE_MM
        if y0 == 1024:
            height[coords >= PANEL_MM - OUTER_BORDER_MM, :] = BASE_MM

        triangles = triangles_for_panel(height)
        output = OUTPUT_DIR / f"demiurge_bas_relief_panel_{name}.stl"
        write_binary_stl(output, triangles, name)
        manifest["panels"][name] = {
            "file": str(output.relative_to(ROOT)),
            "triangle_count": int(len(triangles)),
            "z_min_mm": float(triangles[:, :, 2].min()),
            "z_max_mm": float(triangles[:, :, 2].max()),
            "source_region": [x0, y0, x0 + PANEL_PX, y0 + PANEL_PX],
        }

    (OUTPUT_DIR / "relief_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
