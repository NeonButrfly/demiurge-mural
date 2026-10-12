from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = Path(r"C:\Users\Keifm\OneDrive\Desktop")
OUTPUT_DIR = ROOT / "outputs" / "relief_250_restored"
BASELINE = ROOT / "outputs" / "single" / "demiurge_single_800mm_grayscale.png"
ENHANCED = ROOT / "outputs" / "single" / "demiurge_single_800mm_architecture_depth_enhanced_grayscale.png"
MASK = ROOT / "outputs" / "single" / "demiurge_circular_regions_restoration_mask.png"

STL_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("v0", "<f4", (3,)),
    ("v1", "<f4", (3,)),
    ("v2", "<f4", (3,)),
    ("attribute", "<u2"),
])

PANELS = {
    1: ("panel_1_upper_left.stl", 0, 0),
    2: ("panel_2_upper_right.stl", 1024, 0),
    3: ("panel_3_lower_left.stl", 0, 1024),
    4: ("panel_4_lower_right.stl", 1024, 1024),
}


def read_stl(path: Path) -> tuple[bytes, np.ndarray]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    records = np.frombuffer(data, dtype=STL_DTYPE, count=count, offset=84).copy()
    return data[:84], records


def write_stl(path: Path, header: bytes, records: np.ndarray) -> None:
    normals = np.cross(records["v1"] - records["v0"], records["v2"] - records["v0"])
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    records["normal"] = np.divide(normals, length, out=np.zeros_like(normals), where=length > 0)
    path.write_bytes(header + records.tobytes())


def bilinear(image: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x0 = np.floor(x).astype(int).clip(0, image.shape[1] - 2)
    y0 = np.floor(y).astype(int).clip(0, image.shape[0] - 2)
    dx = x - x0
    dy = y - y0
    a = image[y0, x0]
    b = image[y0, x0 + 1]
    c = image[y0 + 1, x0]
    d = image[y0 + 1, x0 + 1]
    return a * (1 - dx) * (1 - dy) + b * dx * (1 - dy) + c * (1 - dx) * dy + d * dx * dy


def restore_panel(path: Path, panel_number: int, source_x: int, source_y: int) -> tuple[Path, dict]:
    header, records = read_stl(path)
    original_vertices = np.concatenate([records["v0"], records["v1"], records["v2"]], axis=0)
    max_z = float(original_vertices[:, 2].max())
    points = original_vertices.copy()

    baseline = np.asarray(Image.open(BASELINE).convert("L"), dtype=np.float32) / 255.0
    enhanced = np.asarray(Image.open(ENHANCED).convert("L"), dtype=np.float32) / 255.0
    mask = np.asarray(Image.open(MASK).convert("L"), dtype=np.float32) / 255.0

    active = points[:, 2] > 1e-5
    px = source_x + points[:, 0] / 250.0 * 1024.0
    py = source_y + points[:, 1] / 250.0 * 1024.0
    active &= bilinear(mask, px, py) > 0.001
    baseline_height = np.power(bilinear(baseline, px, py).clip(0, 1), 0.30) * max_z
    enhanced_height = np.power(bilinear(enhanced, px, py).clip(0, 1), 0.30) * max_z
    points[active, 2] = np.clip(points[active, 2] + baseline_height[active] - enhanced_height[active], 0.0, max_z)

    records["v0"] = points[: len(points) // 3]
    records["v1"] = points[len(points) // 3 : 2 * len(points) // 3]
    records["v2"] = points[2 * len(points) // 3 :]
    output = OUTPUT_DIR / f"panel_{panel_number}_{['upper_left', 'upper_right', 'lower_left', 'lower_right'][panel_number - 1]}_restored_250mm.stl"
    write_stl(output, header, records)
    changed = np.count_nonzero(np.abs(points[:, 2] - original_vertices[:, 2]) > 1e-6)
    return output, {"input": path.name, "output": output.name, "triangles": int(len(records)), "changed_vertices": int(changed), "bounds_min": points.min(axis=0).tolist(), "bounds_max": points.max(axis=0).tolist()}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"source_dimensions": "250 x 250 mm supplied STL panels", "geometry_policy": "preserve XY coordinates, triangle order, topology, and each input panel Z envelope; local Z-only correction for circles", "panels": {}}
    for number, (name, sx, sy) in PANELS.items():
        source = INPUT_DIR / name
        if not source.exists():
            raise FileNotFoundError(source)
        if number in (3, 4):
            output = OUTPUT_DIR / f"panel_{number}_{['upper_left', 'upper_right', 'lower_left', 'lower_right'][number - 1]}_restored_250mm.stl"
            output.write_bytes(source.read_bytes())
            info = {"input": name, "output": output.name, "byte_identical": True}
        else:
            output, info = restore_panel(source, number, sx, sy)
            info["byte_identical"] = False
        info["input_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
        info["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
        manifest["panels"][str(number)] = info
    (OUTPUT_DIR / "restoration_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
