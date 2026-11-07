import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance


TRI_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("vertices", "<f4", (3, 3)),
    ("attribute", "<u2"),
])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=1200)
    args = parser.parse_args()

    source = args.source.resolve()
    with source.open("rb") as handle:
        handle.seek(80)
        count = struct.unpack("<I", handle.read(4))[0]
    triangles = np.memmap(source, dtype=TRI_DTYPE, mode="r", offset=84, shape=(count,))

    # Known from the inspection pass; derive again without loading the mesh.
    xy_min = np.array([np.inf, np.inf])
    xy_max = np.array([-np.inf, -np.inf])
    z_min, z_max = np.inf, -np.inf
    for start in range(0, count, 300_000):
        v = np.asarray(triangles[start : min(count, start + 300_000)]["vertices"])
        xy_min = np.minimum(xy_min, v[:, :, :2].min(axis=(0, 1)))
        xy_max = np.maximum(xy_max, v[:, :, :2].max(axis=(0, 1)))
        z_min = min(z_min, float(v[:, :, 2].min()))
        z_max = max(z_max, float(v[:, :, 2].max()))

    grid = np.full((args.size, args.size), -np.inf, dtype=np.float32)
    span = xy_max - xy_min
    for start in range(0, count, 200_000):
        v = np.asarray(triangles[start : min(count, start + 200_000)]["vertices"]).reshape(-1, 3)
        px = np.clip(np.rint((v[:, 0] - xy_min[0]) / span[0] * (args.size - 1)), 0, args.size - 1).astype(np.int32)
        py = np.clip(np.rint((v[:, 1] - xy_min[1]) / span[1] * (args.size - 1)), 0, args.size - 1).astype(np.int32)
        np.maximum.at(grid, (py, px), v[:, 2])

    missing = ~np.isfinite(grid)
    # Fill rare downsampling holes from immediate neighbors.
    for _ in range(4):
        if not missing.any():
            break
        candidates = []
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            candidates.append(np.roll(grid, (dy, dx), axis=(0, 1)))
        neighbor = np.maximum.reduce(candidates)
        fill = missing & np.isfinite(neighbor)
        grid[fill] = neighbor[fill]
        missing = ~np.isfinite(grid)
    grid[missing] = z_min

    relief = np.clip((grid - z_min) / max(1e-9, z_max - z_min), 0, 1)
    gy, gx = np.gradient(grid)
    # Soft top-left light for a readable shape preview.
    nx, ny, nz = -gx, gy, np.ones_like(grid) * 2.2
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / length, ny / length, nz / length
    light = np.array([-0.45, -0.35, 0.82])
    shade = np.clip(nx * light[0] + ny * light[1] + nz * light[2], 0, 1)
    image = np.clip(0.20 + 0.46 * relief + 0.42 * shade, 0, 1)
    image = np.flipud(image)
    out = Image.fromarray((image * 255).astype(np.uint8), mode="L")
    out = ImageEnhance.Contrast(out).enhance(1.15)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output)
    height_path = args.output.with_name(args.output.stem + "_height.png")
    Image.fromarray((np.flipud(relief) * 255).astype(np.uint8), mode="L").save(height_path)
    print(args.output)
    print(height_path)


if __name__ == "__main__":
    main()
