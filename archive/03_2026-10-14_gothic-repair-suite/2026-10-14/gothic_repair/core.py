from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


DEFECT_NAMES = [
    "Central feet & shins",
    "Reclining hip/legs",
    "Hooded cybernetic hand",
    "Floating arms",
    "Spear grip",
]


def sha256_array(image: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()


def _png_bytes(array: np.ndarray) -> bytes:
    ok, data = cv2.imencode(".png", array)
    if not ok:
        raise ValueError("Could not encode PNG")
    return data.tobytes()


def _from_png(data: bytes, flags: int = cv2.IMREAD_UNCHANGED) -> np.ndarray:
    value = cv2.imdecode(np.frombuffer(data, np.uint8), flags)
    if value is None:
        raise ValueError("Could not decode PNG")
    return value


def normalize_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    if mask.shape[:2] != shape:
        mask = cv2.resize(mask, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    return np.where(mask > 0, 255, 0).astype(np.uint8)


def strict_composite(original: np.ndarray, candidate: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Composite candidate only inside mask. Outside pixels are copied, not recomputed."""
    if original.shape != candidate.shape:
        raise ValueError("Original and candidate dimensions differ")
    m = normalize_mask(mask, original.shape[:2]) > 0
    result = original.copy()
    result[m] = candidate[m]
    assert np.array_equal(result[~m], original[~m]), "out-of-mask pixels changed"
    return result


def strict_alpha_composite(original: np.ndarray, candidate: np.ndarray, alpha_mask: np.ndarray) -> np.ndarray:
    """Feather inside a grayscale mask while keeping every zero-mask byte untouched."""
    if original.shape != candidate.shape:
        raise ValueError("Original and candidate dimensions differ")
    if alpha_mask.ndim == 3:
        alpha_mask = cv2.cvtColor(alpha_mask, cv2.COLOR_BGR2GRAY)
    if alpha_mask.shape != original.shape[:2]:
        alpha_mask = cv2.resize(alpha_mask, (original.shape[1], original.shape[0]), interpolation=cv2.INTER_LINEAR)
    active = alpha_mask > 0
    alpha = (alpha_mask.astype(np.float32) / 255.0)[..., None]
    blended = np.rint(candidate.astype(np.float32) * alpha + original.astype(np.float32) * (1.0 - alpha))
    result = original.copy()
    result[active] = np.clip(blended[active], 0, 255).astype(np.uint8)
    assert np.array_equal(result[~active], original[~active]), "out-of-mask pixels changed"
    return result


def out_of_mask_diff(baseline: np.ndarray, result: np.ndarray, mask: np.ndarray) -> tuple[int, np.ndarray]:
    if baseline.shape != result.shape:
        raise ValueError("Images must have identical dimensions")
    m = normalize_mask(mask, baseline.shape[:2]) > 0
    changed = np.any(baseline != result, axis=2) & ~m
    visual = np.zeros((*changed.shape, 3), np.uint8)
    visual[changed] = (0, 0, 255)
    return int(changed.sum()), visual


def feather_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    mask = mask.astype(np.uint8)
    if radius <= 0:
        return (mask > 0).astype(np.float32)
    k = max(3, radius * 2 + 1)
    if k % 2 == 0:
        k += 1
    return cv2.GaussianBlur((mask > 0).astype(np.float32), (k, k), max(0.1, radius / 2))


def match_luminance_and_grain(candidate: np.ndarray, reference: np.ndarray, mask: np.ndarray,
                              contrast: float = 1.0, grain: float = 0.0,
                              seed: int = 7) -> np.ndarray:
    """Match masked candidate luminance statistics to a ring around the mask."""
    m = normalize_mask(mask, candidate.shape[:2]) > 0
    if not m.any():
        return candidate.copy()
    ring = cv2.dilate(m.astype(np.uint8), np.ones((17, 17), np.uint8), iterations=1).astype(bool) & ~m
    if not ring.any():
        ring = ~m
    out = candidate.astype(np.float32)
    cand_gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY).astype(np.float32)
    c_mean, c_std = float(cand_gray[m].mean()), float(cand_gray[m].std() + 1e-6)
    r_mean, r_std = float(ref_gray[ring].mean()), float(ref_gray[ring].std() + 1e-6)
    scale = (r_std / c_std) * float(contrast)
    for channel in range(out.shape[2]):
        vals = out[..., channel]
        vals[m] = (vals[m] - c_mean) * scale + r_mean
    if grain > 0:
        noise = np.random.default_rng(seed).normal(0, grain, m.sum()).astype(np.float32)
        for channel in range(out.shape[2]):
            out[..., channel][m] += noise
    return np.clip(out, 0, 255).astype(np.uint8)


def transform_patch(image: np.ndarray, source_rect: tuple[int, int, int, int],
                    center: tuple[int, int], angle: float = 0, scale: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    x, y, w, h = source_rect
    patch = image[max(0, y):max(0, y) + h, max(0, x):max(0, x) + w]
    if patch.size == 0:
        raise ValueError("Donor rectangle is empty")
    alpha = np.full(patch.shape[:2], 255, np.uint8)
    rot = cv2.getRotationMatrix2D((patch.shape[1] / 2, patch.shape[0] / 2), angle, scale)
    bounds = cv2.warpAffine(patch, rot, (patch.shape[1], patch.shape[0]), flags=cv2.INTER_LANCZOS4)
    bounds_a = cv2.warpAffine(alpha, rot, (patch.shape[1], patch.shape[0]), flags=cv2.INTER_LINEAR)
    canvas = image.copy()
    donor_mask = np.zeros(image.shape[:2], np.uint8)
    tx, ty = int(center[0] - bounds.shape[1] / 2), int(center[1] - bounds.shape[0] / 2)
    x0, y0 = max(0, tx), max(0, ty)
    x1, y1 = min(image.shape[1], tx + bounds.shape[1]), min(image.shape[0], ty + bounds.shape[0])
    if x1 <= x0 or y1 <= y0:
        return canvas, donor_mask
    px0, py0 = x0 - tx, y0 - ty
    px1, py1 = px0 + x1 - x0, py0 + y1 - y0
    a = bounds_a[py0:py1, px0:px1] > 0
    roi = canvas[y0:y1, x0:x1]
    roi[a] = bounds[py0:py1, px0:px1][a]
    donor_mask[y0:y1, x0:x1][a] = 255
    return canvas, donor_mask


@dataclass
class Region:
    id: int
    name: str
    status: str = "pending"
    notes: str = ""
    mask: np.ndarray | None = field(default=None, repr=False, compare=False)


@dataclass
class Candidate:
    name: str
    image: np.ndarray = field(repr=False, compare=False)
    mask: np.ndarray = field(repr=False, compare=False)
    backend: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)


class RepairProject:
    def __init__(self, original: np.ndarray, source_path: str = ""):
        if original is None or original.ndim != 3:
            raise ValueError("A color source image is required")
        self.original = original.copy()
        self.working = original.copy()
        self.source_path = source_path
        self.original_sha256 = sha256_array(self.original)
        self.regions = [Region(i + 1, name, mask=np.zeros(original.shape[:2], np.uint8))
                        for i, name in enumerate(DEFECT_NAMES)]
        self.active_region = 1
        self.candidate: Candidate | None = None
        self.history: list[bytes] = [_png_bytes(self.working)]
        self.history_labels: list[str] = ["Original"]
        self.history_index = 0

    @classmethod
    def from_file(cls, path: str | Path) -> "RepairProject":
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise FileNotFoundError(path)
        return cls(image, str(Path(path).resolve()))

    @property
    def region(self) -> Region:
        return self.regions[self.active_region - 1]

    def set_mask(self, mask: np.ndarray) -> None:
        self.region.mask = normalize_mask(mask, self.original.shape[:2])

    def combined_approved_mask(self) -> np.ndarray:
        out = np.zeros(self.original.shape[:2], np.uint8)
        for region in self.regions:
            if region.status == "approved" and region.mask is not None:
                out = cv2.bitwise_or(out, region.mask)
        return out

    def set_candidate(self, image: np.ndarray, mask: np.ndarray, name: str,
                      backend: str, metadata: dict[str, Any] | None = None) -> Candidate:
        self.candidate = Candidate(name, image.copy(), normalize_mask(mask, self.original.shape[:2]),
                                   backend, metadata or {})
        return self.candidate

    def approve_candidate(self) -> None:
        if self.candidate is None:
            raise ValueError("No candidate is active")
        self.working = strict_composite(self.working, self.candidate.image, self.candidate.mask)
        self.region.status = "approved"
        self.region.mask = cv2.bitwise_or(self.region.mask, self.candidate.mask)
        self._checkpoint(f"Approved {self.region.id}: {self.candidate.name}")
        self.candidate = None

    def reject_candidate(self) -> None:
        self.candidate = None

    def _checkpoint(self, label: str) -> None:
        del self.history[self.history_index + 1:]
        del self.history_labels[self.history_index + 1:]
        self.history.append(_png_bytes(self.working))
        self.history_labels.append(label)
        self.history_index += 1

    def checkpoint(self, label: str) -> None:
        self._checkpoint(label)

    def undo(self) -> bool:
        if self.history_index == 0:
            return False
        self.history_index -= 1
        self.working = _from_png(self.history[self.history_index], cv2.IMREAD_COLOR)
        return True

    def redo(self) -> bool:
        if self.history_index >= len(self.history) - 1:
            return False
        self.history_index += 1
        self.working = _from_png(self.history[self.history_index], cv2.IMREAD_COLOR)
        return True

    def goto_history(self, index: int) -> bool:
        if not 0 <= index < len(self.history):
            return False
        self.history_index = index
        self.working = _from_png(self.history[index], cv2.IMREAD_COLOR)
        return True

    def assert_invariant(self) -> int:
        count, _ = out_of_mask_diff(self.original, self.working, self.combined_approved_mask())
        if count:
            raise AssertionError(f"{count} pixels changed outside approved masks")
        return count

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path / "original.png"), self.original)
        cv2.imwrite(str(path / "working.png"), self.working)
        masks = path / "masks"
        masks.mkdir(exist_ok=True)
        for region in self.regions:
            cv2.imwrite(str(masks / f"region_{region.id}.png"), region.mask)
        meta = {
            "version": 1, "source_path": self.source_path, "original_sha256": self.original_sha256,
            "active_region": self.active_region, "history_index": self.history_index,
            "history_labels": self.history_labels,
            "history": [base64.b64encode(x).decode("ascii") for x in self.history],
            "regions": [{k: v for k, v in asdict(r).items() if k != "mask"} for r in self.regions],
        }
        (path / "project.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "RepairProject":
        path = Path(path)
        meta = json.loads((path / "project.json").read_text(encoding="utf-8"))
        original = cv2.imread(str(path / "original.png"), cv2.IMREAD_COLOR)
        project = cls(original, meta.get("source_path", ""))
        if project.original_sha256 != meta["original_sha256"]:
            raise ValueError("Original image checksum mismatch")
        project.working = cv2.imread(str(path / "working.png"), cv2.IMREAD_COLOR)
        project.regions = []
        for item in meta["regions"]:
            mask = cv2.imread(str(path / "masks" / f"region_{item['id']}.png"), cv2.IMREAD_GRAYSCALE)
            project.regions.append(Region(**item, mask=mask))
        project.active_region = meta["active_region"]
        project.history = [base64.b64decode(x) for x in meta["history"]]
        project.history_labels = meta["history_labels"]
        project.history_index = meta["history_index"]
        project.candidate = None
        return project

    def export(self, path: str | Path, size: int | None = 2048) -> Path:
        self.assert_invariant()
        image = self.working
        if size:
            image = cv2.resize(image, (size, size), interpolation=cv2.INTER_LANCZOS4)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        return path

    def export_heightmap(self, path: str | Path, size: int | None = 2048) -> Path:
        gray = cv2.cvtColor(self.working, cv2.COLOR_BGR2GRAY)
        if size:
            gray = cv2.resize(gray, (size, size), interpolation=cv2.INTER_LANCZOS4)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(gray).save(path, bits=16)
        return path
