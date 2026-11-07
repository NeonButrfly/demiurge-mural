import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gothic_repair.ui import MainWindow


def test_window_loads_pass7_assets():
    app = QApplication.instance() or QApplication([])
    root = Path(__file__).parents[1]
    window = MainWindow(root / "assets" / "Gothic_Relief_Pass_7_Original.png",
                        root / "assets" / "Pass7_Central_Legs_Inpaint_Mask.png")
    assert window.project is not None
    assert window.project.working.shape == (1254, 1254, 3)
    assert window.project.region.mask.any()
    assert "opencv" in window.backends
    window.close()

