from __future__ import annotations

import base64
import importlib.util
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
import requests

from .core import normalize_mask


class InpaintBackend(ABC):
    name = "base"

    @abstractmethod
    def inpaint(self, image: np.ndarray, mask: np.ndarray, prompt: str = "", **options) -> np.ndarray:
        raise NotImplementedError


class OpenCVBackend(InpaintBackend):
    """Always-available real local mask-aware content propagation."""
    name = "opencv"

    def inpaint(self, image: np.ndarray, mask: np.ndarray, prompt: str = "", **options) -> np.ndarray:
        method = cv2.INPAINT_NS if options.get("method") == "ns" else cv2.INPAINT_TELEA
        radius = float(options.get("radius", 3.0))
        return cv2.inpaint(image, normalize_mask(mask, image.shape[:2]), radius, method)


class RemoteEndpointBackend(InpaintBackend):
    """POSTs PNG image/mask and receives PNG bytes or {image_base64: ...}."""
    name = "remote"

    def __init__(self, url: str, token: str = "", timeout: int = 180):
        self.url, self.token, self.timeout = url, token, timeout

    def inpaint(self, image: np.ndarray, mask: np.ndarray, prompt: str = "", **options) -> np.ndarray:
        _, image_png = cv2.imencode(".png", image)
        _, mask_png = cv2.imencode(".png", normalize_mask(mask, image.shape[:2]))
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        files = {"image": ("image.png", image_png.tobytes(), "image/png"),
                 "mask": ("mask.png", mask_png.tobytes(), "image/png")}
        response = requests.post(self.url, headers=headers, files=files,
                                 data={"prompt": prompt, "options": json.dumps(options)}, timeout=self.timeout)
        response.raise_for_status()
        data = response.content
        if "json" in response.headers.get("content-type", ""):
            data = base64.b64decode(response.json()["image_base64"])
        result = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if result is None:
            raise ValueError("Endpoint returned no decodable image")
        return cv2.resize(result, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LANCZOS4)


def discover_plugins(folder: str | Path) -> dict[str, InpaintBackend]:
    """Load BACKEND objects from user-owned Python files in a configured plugin folder."""
    result: dict[str, InpaintBackend] = {"opencv": OpenCVBackend()}
    folder = Path(folder)
    if not folder.exists():
        return result
    for file in folder.glob("*.py"):
        if file.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"repair_plugin_{file.stem}", file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            backend = getattr(module, "BACKEND", None)
            if isinstance(backend, InpaintBackend):
                result[backend.name] = backend
    endpoint = os.getenv("GOTHIC_REPAIR_ENDPOINT")
    if endpoint:
        result["remote"] = RemoteEndpointBackend(endpoint, os.getenv("GOTHIC_REPAIR_TOKEN", ""))
    return result

