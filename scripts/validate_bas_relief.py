from __future__ import annotations

import struct
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RELIEF_DIR = ROOT / "outputs" / "relief"
STL_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("v0", "<f4", (3,)),
    ("v1", "<f4", (3,)),
    ("v2", "<f4", (3,)),
    ("attribute", "<u2"),
])
EDGE_DTYPE = np.dtype([
    ("a0", "<i8"), ("a1", "<i8"), ("a2", "<i8"),
    ("b0", "<i8"), ("b1", "<i8"), ("b2", "<i8"),
])


def validate(path: Path) -> tuple[int, tuple[float, ...], int]:
    with path.open("rb") as handle:
        header = handle.read(80)
        count = struct.unpack("<I", handle.read(4))[0]
    records = np.fromfile(path, dtype=STL_DTYPE, count=count, offset=84)
    vertices = np.stack((records["v0"], records["v1"], records["v2"]), axis=1)
    bounds_min = vertices.min(axis=(0, 1))
    bounds_max = vertices.max(axis=(0, 1))
    if not np.allclose(bounds_min, [0.0, 0.0, 0.0], atol=1e-4):
        raise AssertionError(f"{path.name}: unexpected minimum bounds {bounds_min}")
    if not np.allclose(bounds_max[:2], [400.0, 400.0], atol=1e-4):
        raise AssertionError(f"{path.name}: unexpected XY maximum bounds {bounds_max}")
    if not (9.99 <= bounds_max[2] <= 10.01):
        raise AssertionError(f"{path.name}: unexpected Z maximum {bounds_max[2]}")

    # Quantize coordinates to 0.01 micrometre to make shared STL vertices
    # comparable, then verify every undirected edge belongs to two triangles.
    quantized = np.rint(vertices * 100000.0).astype(np.int64)
    edges = np.concatenate((quantized[:, [0, 1]], quantized[:, [1, 2]], quantized[:, [2, 0]]), axis=0)
    swap = (
        (edges[:, 0, 0] > edges[:, 1, 0])
        | ((edges[:, 0, 0] == edges[:, 1, 0]) & (edges[:, 0, 1] > edges[:, 1, 1]))
        | ((edges[:, 0, 0] == edges[:, 1, 0]) & (edges[:, 0, 1] == edges[:, 1, 1]) & (edges[:, 0, 2] > edges[:, 1, 2]))
    )
    edges[swap] = edges[swap][:, ::-1]
    keys = np.empty(len(edges), dtype=EDGE_DTYPE)
    keys["a0"], keys["a1"], keys["a2"] = edges[:, 0, 0], edges[:, 0, 1], edges[:, 0, 2]
    keys["b0"], keys["b1"], keys["b2"] = edges[:, 1, 0], edges[:, 1, 1], edges[:, 1, 2]
    _, counts = np.unique(keys, return_counts=True)
    if not np.all(counts == 2):
        raise AssertionError(f"{path.name}: non-manifold edge counts {np.unique(counts, return_counts=True)}")
    return count, tuple(float(value) for value in bounds_max), len(counts)


def main() -> None:
    for path in sorted(RELIEF_DIR.glob("*.stl")):
        count, bounds, edges = validate(path)
        print(f"{path.name}: triangles={count} bounds_max={bounds} manifold_edges={edges}")


if __name__ == "__main__":
    main()
