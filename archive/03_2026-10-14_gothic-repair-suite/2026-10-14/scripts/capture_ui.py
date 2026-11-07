"""Render the real desktop window offscreen for release evidence."""
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gothic_repair.ui import MainWindow


ROOT = Path(__file__).parents[1]


def main():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(ROOT / "assets" / "Gothic_Relief_Pass_7_Original.png",
                        ROOT / "assets" / "Pass7_Central_Legs_Inpaint_Mask.png")
    window.show()
    app.processEvents()
    output = ROOT / "outputs" / "tested_pass7" / "Gothic_Repair_Suite_UI.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not window.grab().save(str(output)):
        raise RuntimeError("Could not save UI capture")
    window.close()
    print(output)


if __name__ == "__main__":
    main()
