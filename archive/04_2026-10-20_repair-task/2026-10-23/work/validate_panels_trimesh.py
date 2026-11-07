import gc
import json
import sys
from pathlib import Path

import trimesh


def main():
    folder = Path(sys.argv[1]).resolve()
    results = []
    for path in sorted(folder.glob("panel_*_X2D_*mm.stl")):
        mesh = trimesh.load_mesh(path, process=True)
        result = {
            "file": str(path),
            "vertices_after_merge": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "watertight": bool(mesh.is_watertight),
            "winding_consistent": bool(mesh.is_winding_consistent),
            "is_volume": bool(mesh.is_volume),
            "body_count": int(mesh.body_count),
            "euler_number": int(mesh.euler_number),
            "volume_mm3": float(mesh.volume),
            "bounds": mesh.bounds.tolist(),
            "extents": mesh.extents.tolist(),
        }
        print(json.dumps(result), flush=True)
        results.append(result)
        del mesh
        gc.collect()
    out = folder / "trimesh_manifold_validation.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if not results or not all(r["watertight"] and r["winding_consistent"] and r["is_volume"] and r["body_count"] == 1 for r in results):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
