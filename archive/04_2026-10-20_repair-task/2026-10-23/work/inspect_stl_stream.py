import argparse
import json
import struct
from pathlib import Path

import numpy as np


TRI_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("vertices", "<f4", (3, 3)),
    ("attribute", "<u2"),
])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chunk", type=int, default=250_000)
    args = parser.parse_args()

    source = args.source.resolve()
    size = source.stat().st_size
    with source.open("rb") as handle:
        header = handle.read(80)
        count = struct.unpack("<I", handle.read(4))[0]
    expected = 84 + count * 50
    if expected != size:
        raise ValueError(f"Not a standard binary STL: expected {expected} bytes, got {size}")

    triangles = np.memmap(source, dtype=TRI_DTYPE, mode="r", offset=84, shape=(count,))
    bounds_min = np.full(3, np.inf)
    bounds_max = np.full(3, -np.inf)
    degenerate = 0
    zero_stored_normals = 0
    area_sum = 0.0
    axis_normal_sum = np.zeros(3, dtype=np.float64)
    sample_parts = []

    sample_stride = max(1, count // 1_000_000)
    for start in range(0, count, args.chunk):
        block = triangles[start : min(count, start + args.chunk)]
        vertices = np.asarray(block["vertices"], dtype=np.float64)
        bounds_min = np.minimum(bounds_min, vertices.min(axis=(0, 1)))
        bounds_max = np.maximum(bounds_max, vertices.max(axis=(0, 1)))
        cross = np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0])
        twice_area = np.linalg.norm(cross, axis=1)
        degenerate += int(np.count_nonzero(twice_area <= 1e-12))
        area_sum += float(0.5 * twice_area.sum())
        nz = twice_area > 1e-12
        if np.any(nz):
            axis_normal_sum += np.abs(cross[nz] / twice_area[nz, None]).sum(axis=0)
        stored = np.asarray(block["normal"], dtype=np.float64)
        zero_stored_normals += int(np.count_nonzero(np.linalg.norm(stored, axis=1) <= 1e-12))
        local = vertices[::sample_stride].reshape(-1, 3)
        if len(local):
            sample_parts.append(local[: max(1, 1_000_000 // max(1, count // args.chunk))])

    extents = bounds_max - bounds_min
    thin_axis = int(np.argmin(extents))
    plane_axes = [i for i in range(3) if i != thin_axis]
    # Put the longer plane dimension first for a predictable display orientation.
    plane_axes.sort(key=lambda i: (-extents[i], i))
    samples = np.concatenate(sample_parts, axis=0) if sample_parts else np.empty((0, 3))
    percentiles = {}
    if len(samples):
        for axis in range(3):
            percentiles[str(axis)] = {
                str(p): float(np.percentile(samples[:, axis], p))
                for p in (0, 1, 5, 25, 50, 75, 95, 99, 100)
            }

    report = {
        "source": str(source),
        "file_size_bytes": size,
        "format": "binary_stl",
        "triangle_count": count,
        "bounds_min": bounds_min.tolist(),
        "bounds_max": bounds_max.tolist(),
        "extents": extents.tolist(),
        "thin_axis": thin_axis,
        "plane_axes": plane_axes,
        "surface_area": area_sum,
        "degenerate_triangles": degenerate,
        "stored_zero_normals": zero_stored_normals,
        "mean_absolute_unit_normal_by_axis": (axis_normal_sum / max(1, count - degenerate)).tolist(),
        "sampled_vertex_percentiles": percentiles,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
