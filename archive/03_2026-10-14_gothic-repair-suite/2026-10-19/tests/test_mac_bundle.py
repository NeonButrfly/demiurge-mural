import hashlib
from pathlib import Path

import cv2
import pytest

from gothic_repair import app


ROOT = Path(__file__).parents[1]
CURRENT = ROOT / "assets" / "current" / "Demiurge_Current_2048_2026-10-19.png"


def test_current_mac_handoff_image_is_exact_2048_source():
    image = cv2.imread(str(CURRENT), cv2.IMREAD_COLOR)
    assert image.shape == (2048, 2048, 3)
    assert hashlib.sha256(CURRENT.read_bytes()).hexdigest() == (
        "3d6022dafe77d6a93fcf5dac1a6ac6f70b0a29ab2d7dca419c6b058a42f6764c"
    )


def test_cli_can_open_an_explicit_source_without_a_mask(monkeypatch):
    captured = {}

    def fake_run(source, mask):
        captured["source"] = source
        captured["mask"] = mask
        return 0

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(app, "run", fake_run)
    with pytest.raises(SystemExit) as result:
        app.main(["--source", str(CURRENT), "--mask", "missing-mask.png"])
    assert result.value.code == 0
    assert captured == {"source": CURRENT, "mask": None}


def test_mac_handoff_files_are_present_and_use_lf():
    for name in ("setup_mac.sh", "launch_mac.sh", "run_tests_mac.sh"):
        data = (ROOT / name).read_bytes()
        assert data.startswith(b"#!/usr/bin/env bash\n")
        assert b"\r\n" not in data
    assert (ROOT / "MAC_CONTINUATION.md").is_file()
    assert (ROOT / "docs" / "prompts" / "current-master-repair-instructions.md").is_file()
