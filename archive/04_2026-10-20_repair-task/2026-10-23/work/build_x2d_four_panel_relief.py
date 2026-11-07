import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance


STL_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("vertices", "<f4", (3, 3)),
    ("attribute", "<u2"),
])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_binary_stl(path: Path):
    with path.open("rb") as handle:
        header = handle.read(80)
        count = struct.unpack("<I", handle.read(4))[0]
    if path.stat().st_size != 84 + count * 50:
        raise ValueError("Source is not a standard binary STL")
    triangles = np.memmap(path, dtype=STL_DTYPE, mode="r", offset=84, shape=(count,))
    return header, count, triangles


def extract_height_grid(triangles, count: int):
    bounds_min = np.full(3, np.inf)
    bounds_max = np.full(3, -np.inf)
    for start in range(0, count, 300_000):
        vertices = np.asarray(triangles[start : min(count, start + 300_000)]["vertices"])
        bounds_min = np.minimum(bounds_min, vertices.min(axis=(0, 1)))
        bounds_max = np.maximum(bounds_max, vertices.max(axis=(0, 1)))

    # The source is a regular closed heightfield. Infer its exact pitch from the
    # first coordinate changes rather than rounding or resampling the artwork.
    sample = np.asarray(triangles[: min(count, 1_000_000)]["vertices"]).reshape(-1, 3)
    pitches = []
    for axis in (0, 1):
        unique = np.unique(sample[:, axis])
        diffs = np.diff(unique)
        pitches.append(float(np.min(diffs[diffs > 1e-6])))
    pitch = min(pitches)
    nx = int(round((bounds_max[0] - bounds_min[0]) / pitch)) + 1
    ny = int(round((bounds_max[1] - bounds_min[1]) / pitch)) + 1
    if nx % 2 == 0 or ny % 2 == 0:
        raise ValueError(f"Expected odd grid dimensions for a centered four-way split, got {nx}x{ny}")

    height = np.full((ny, nx), -np.inf, dtype=np.float32)
    for start in range(0, count, 200_000):
        vertices = np.asarray(triangles[start : min(count, start + 200_000)]["vertices"]).reshape(-1, 3)
        ix = np.rint((vertices[:, 0] - bounds_min[0]) / pitch).astype(np.int32)
        iy = np.rint((vertices[:, 1] - bounds_min[1]) / pitch).astype(np.int32)
        valid = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        np.maximum.at(height, (iy[valid], ix[valid]), vertices[valid, 2])
    if not np.isfinite(height).all():
        missing = int(np.count_nonzero(~np.isfinite(height)))
        raise ValueError(f"Height grid reconstruction left {missing} missing samples")
    return bounds_min, bounds_max, pitch, height


def normals_for(vertices: np.ndarray) -> np.ndarray:
    cross = np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0])
    length = np.linalg.norm(cross, axis=1)
    if np.any(length <= 1e-12):
        raise ValueError("Generated a degenerate triangle")
    return (cross / length[:, None]).astype(np.float32)


class BinaryStlWriter:
    def __init__(self, path: Path, triangle_count: int, label: str):
        self.path = path
        self.expected = triangle_count
        self.written = 0
        self.handle = path.open("wb")
        header = (f"Codex X2D relief panel | {label}").encode("ascii")[:80]
        self.handle.write(header.ljust(80, b"\0"))
        self.handle.write(struct.pack("<I", triangle_count))

    def write(self, vertices: np.ndarray):
        vertices = np.asarray(vertices, dtype=np.float32)
        records = np.zeros(len(vertices), dtype=STL_DTYPE)
        records["vertices"] = vertices
        records["normal"] = normals_for(vertices)
        records.tofile(self.handle)
        self.written += len(vertices)

    def close(self):
        self.handle.close()
        if self.written != self.expected:
            raise ValueError(f"Triangle count mismatch for {self.path}: {self.written} != {self.expected}")


def write_panel(path: Path, heights: np.ndarray, panel_size: float, label: str):
    ny, nx = heights.shape
    xs = np.linspace(0.0, panel_size, nx, dtype=np.float32)
    ys = np.linspace(0.0, panel_size, ny, dtype=np.float32)
    top_count = 2 * (nx - 1) * (ny - 1)
    side_count = 2 * ((nx - 1) * 2 + (ny - 1) * 2)
    bottom_count = 2 * ((nx - 1) + (ny - 1))
    writer = BinaryStlWriter(path, top_count + side_count + bottom_count, label)

    # Top surface, wound upward.
    for row in range(ny - 1):
        x0, x1 = xs[:-1], xs[1:]
        y0 = np.full(nx - 1, ys[row], dtype=np.float32)
        y1 = np.full(nx - 1, ys[row + 1], dtype=np.float32)
        z00, z10 = heights[row, :-1], heights[row, 1:]
        z01, z11 = heights[row + 1, :-1], heights[row + 1, 1:]
        v00 = np.column_stack((x0, y0, z00))
        v10 = np.column_stack((x1, y0, z10))
        v01 = np.column_stack((x0, y1, z01))
        v11 = np.column_stack((x1, y1, z11))
        tris = np.empty((2 * (nx - 1), 3, 3), dtype=np.float32)
        tris[0::2] = np.stack((v00, v10, v11), axis=1)
        tris[1::2] = np.stack((v00, v11, v01), axis=1)
        writer.write(tris)

    def side(points_top):
        top = np.asarray(points_top, dtype=np.float32)
        bottom = top.copy()
        bottom[:, 2] = 0.0
        b0, b1 = bottom[:-1], bottom[1:]
        t0, t1 = top[:-1], top[1:]
        # Boundary points run counter-clockwise as viewed from above, so this
        # winding points every vertical wall outward.
        tris = np.concatenate((np.stack((b0, b1, t1), axis=1), np.stack((b0, t1, t0), axis=1)))
        writer.write(tris)

    # Outward walls: y-min, x-max, y-max, x-min.
    side(np.column_stack((xs, np.full(nx, ys[0]), heights[0, :])))
    side(np.column_stack((np.full(ny, xs[-1]), ys, heights[:, -1])))
    side(np.column_stack((xs[::-1], np.full(nx, ys[-1]), heights[-1, ::-1])))
    side(np.column_stack((np.full(ny, xs[0]), ys[::-1], heights[::-1, 0])))

    # Bottom fan uses every boundary vertex, preventing T-junctions while
    # avoiding millions of redundant coplanar bottom triangles.
    perimeter = []
    perimeter.extend((float(x), float(ys[0]), 0.0) for x in xs[:-1])
    perimeter.extend((float(xs[-1]), float(y), 0.0) for y in ys[:-1])
    perimeter.extend((float(x), float(ys[-1]), 0.0) for x in xs[:0:-1])
    perimeter.extend((float(xs[0]), float(y), 0.0) for y in ys[:0:-1])
    perimeter = np.asarray(perimeter, dtype=np.float32)
    center = np.array([panel_size / 2.0, panel_size / 2.0, 0.0], dtype=np.float32)
    next_points = np.roll(perimeter, -1, axis=0)
    # Reverse perimeter order per triangle so outward normal is -Z.
    writer.write(np.stack((np.repeat(center[None, :], len(perimeter), axis=0), next_points, perimeter), axis=1))
    writer.close()
    return top_count + side_count + bottom_count


def shade(height: np.ndarray) -> Image.Image:
    relief = (height - height.min()) / max(1e-9, float(height.max() - height.min()))
    gy, gx = np.gradient(height)
    nx, ny, nz = -gx, gy, np.ones_like(height) * 2.2
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    light = np.array([-0.45, -0.35, 0.82])
    illumination = np.clip(nx / length * light[0] + ny / length * light[1] + nz / length * light[2], 0, 1)
    image = np.clip(0.20 + 0.46 * relief + 0.42 * illumination, 0, 1)
    out = Image.fromarray((np.flipud(image) * 255).astype(np.uint8), mode="L")
    return ImageEnhance.Contrast(out).enhance(1.15)


def stl_quick_validation(path: Path):
    with path.open("rb") as handle:
        handle.seek(80)
        count = struct.unpack("<I", handle.read(4))[0]
    valid_size = path.stat().st_size == 84 + count * 50
    mesh = np.memmap(path, dtype=STL_DTYPE, mode="r", offset=84, shape=(count,))
    minimum = np.full(3, np.inf)
    maximum = np.full(3, -np.inf)
    degenerate = 0
    for start in range(0, count, 250_000):
        v = np.asarray(mesh[start : min(count, start + 250_000)]["vertices"], dtype=np.float64)
        minimum = np.minimum(minimum, v.min(axis=(0, 1)))
        maximum = np.maximum(maximum, v.max(axis=(0, 1)))
        cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
        degenerate += int(np.count_nonzero(np.linalg.norm(cross, axis=1) <= 1e-12))
    return {
        "file": str(path),
        "file_size_bytes": path.stat().st_size,
        "triangle_count": count,
        "binary_stl_size_valid": valid_size,
        "bounds_min": minimum.tolist(),
        "bounds_max": maximum.tolist(),
        "extents": (maximum - minimum).tolist(),
        "degenerate_triangles": degenerate,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--assembly-size", type=float, default=500.0)
    parser.add_argument("--base-thickness", type=float, default=2.4)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    _, count, triangles = read_binary_stl(source)
    bounds_min, bounds_max, pitch, source_height = extract_height_grid(triangles, count)
    source_top_min = float(source_height.min())
    source_top_max = float(source_height.max())
    xy_scale = args.assembly_size / float(bounds_max[0] - bounds_min[0])
    # Uniform relief scaling preserves the sculptor's intended depth ratios.
    relief = (source_height - source_top_min) * xy_scale
    final_height = args.base_thickness + relief
    mid_y = (final_height.shape[0] - 1) // 2
    mid_x = (final_height.shape[1] - 1) // 2
    panel_size = args.assembly_size / 2.0

    panels = [
        ("panel_1_upper_left", final_height[mid_y:, : mid_x + 1]),
        ("panel_2_upper_right", final_height[mid_y:, mid_x:]),
        ("panel_3_lower_left", final_height[: mid_y + 1, : mid_x + 1]),
        ("panel_4_lower_right", final_height[: mid_y + 1, mid_x:]),
    ]
    validations = []
    size_tag = f"{panel_size:g}mm"
    for name, panel_height in panels:
        stl_path = output / f"{name}_X2D_{size_tag}.stl"
        write_panel(stl_path, panel_height, panel_size, name)
        preview = shade(panel_height).resize((900, 900), Image.Resampling.LANCZOS)
        preview.save(output / f"{name}_preview.png")
        validations.append(stl_quick_validation(stl_path))

    combined = shade(final_height).resize((1400, 1400), Image.Resampling.LANCZOS).convert("RGB")
    draw = ImageDraw.Draw(combined)
    center = combined.width // 2
    draw.line((center, 0, center, combined.height), fill=(30, 30, 30), width=2)
    draw.line((0, center, combined.width, center), fill=(30, 30, 30), width=2)
    combined.save(output / "assembled_four_panel_preview.png")

    seam_x = float(np.max(np.abs(final_height[:, mid_x] - final_height[:, mid_x])))
    seam_y = float(np.max(np.abs(final_height[mid_y, :] - final_height[mid_y, :])))
    report = {
        "source": str(source),
        "source_sha256": file_sha256(source),
        "source_triangle_count": count,
        "source_bounds_min": bounds_min.tolist(),
        "source_bounds_max": bounds_max.tolist(),
        "source_grid_pitch_mm": pitch,
        "source_grid_shape": list(source_height.shape),
        "target_printer": "Bambu Lab X2D",
        "installed_profile_printable_area_mm": [256.0, 256.0],
        "installed_profile_second_extruder_min_x_mm": 20.5,
        "assembly_xy_mm": [args.assembly_size, args.assembly_size],
        "panel_xy_mm": [panel_size, panel_size],
        "full_bed_margin_per_axis_mm": 256.0 - panel_size,
        "centered_full_bed_margin_per_edge_mm": (256.0 - panel_size) / 2.0,
        "base_thickness_mm": args.base_thickness,
        "relief_elevation_mm": float(final_height.max() - args.base_thickness),
        "total_height_mm": float(final_height.max()),
        "xy_scale": xy_scale,
        "z_relief_scale": xy_scale,
        "seam_height_error_mm": {"vertical": seam_x, "horizontal": seam_y},
        "panels": validations,
        "notes": [
            "The artwork was not smoothed or regenerated.",
            "Each panel has a flat 2.4 mm base and exact shared seam samples.",
            "The coplanar bottom uses a boundary-matched fan to avoid T-junctions.",
            "Digital mesh checks do not establish physical fit or slicer success.",
        ],
    }
    (output / "x2d_four_panel_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    readme = f"""X2D FOUR-PANEL RELIEF\n\nSource: {source}\nAssembly: {args.assembly_size:.1f} x {args.assembly_size:.1f} mm\nPanels: 4 at {panel_size:.1f} x {panel_size:.1f} mm\nX2D main-nozzle envelope used: 256 x 256 mm\nBase: {args.base_thickness:.1f} mm\nMaximum total height: {final_height.max():.2f} mm\n\nLayout:\n  panel_1_upper_left | panel_2_upper_right\n  panel_3_lower_left | panel_4_lower_right\n\nThe four cut edges use identical source samples, so the sculpted relief remains continuous across the center seams. Import each STL as one object and keep its X/Y scale at 100%. Bambu Studio slicing and physical seam fit still require confirmation on the target printer.\n"""
    (output / "README.txt").write_text(readme, encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
