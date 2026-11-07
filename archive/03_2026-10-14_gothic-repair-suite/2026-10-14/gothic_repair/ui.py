from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QImage, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QHBoxLayout, QInputDialog, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QToolBar, QVBoxLayout, QWidget,
)

from .backends import discover_plugins
from .core import RepairProject, feather_mask, match_luminance_and_grain, out_of_mask_diff, transform_patch
from .qa import make_qa_bundle


def to_qimage(bgr: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, c = rgb.shape
    return QImage(rgb.data, w, h, w * c, QImage.Format.Format_RGB888).copy()


class Canvas(QWidget):
    maskChanged = Signal()
    positionChanged = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.image: np.ndarray | None = None
        self.mask: np.ndarray | None = None
        self.zoom = 0.75
        self.offset = QPointF(20, 20)
        self.mode = "brush"
        self.brush = 32
        self.overlay = True
        self.drawing = False
        self.last_image_point: tuple[int, int] | None = None
        self.pan_start = QPoint()
        self.poly: list[tuple[int, int]] = []
        self.setMouseTracking(True)
        self.setMinimumSize(640, 640)

    def set_data(self, image: np.ndarray, mask: np.ndarray):
        self.image = image
        self.mask = mask
        self.update()

    def image_point(self, point: QPointF) -> tuple[int, int] | None:
        if self.image is None:
            return None
        x = int((point.x() - self.offset.x()) / self.zoom)
        y = int((point.y() - self.offset.y()) / self.zoom)
        if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
            return x, y
        return None

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#202225"))
        if self.image is None:
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Open an image")
            return
        shown = self.image.copy()
        if self.overlay and self.mask is not None:
            active = self.mask > 0
            shown[active] = (shown[active].astype(np.float32) * .55 + np.array([25, 25, 255]) * .45).astype(np.uint8)
        target = QImage(to_qimage(shown)).scaled(int(shown.shape[1] * self.zoom), int(shown.shape[0] * self.zoom),
                                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                                   Qt.TransformationMode.FastTransformation if self.zoom >= 1 else Qt.TransformationMode.SmoothTransformation)
        painter.drawImage(self.offset, target)
        if self.poly:
            painter.setPen(QPen(QColor("#00ffff"), 2))
            pts = [QPoint(int(self.offset.x() + x * self.zoom), int(self.offset.y() + y * self.zoom)) for x, y in self.poly]
            painter.drawPolyline(QPolygon(pts))

    def wheelEvent(self, event):
        if self.image is None:
            return
        before = self.image_point(event.position())
        factor = 1.25 if event.angleDelta().y() > 0 else .8
        self.zoom = min(16.0, max(.05, self.zoom * factor))
        if before:
            self.offset = QPointF(event.position().x() - before[0] * self.zoom,
                                  event.position().y() - before[1] * self.zoom)
        self.update()

    def mousePressEvent(self, event):
        p = self.image_point(event.position())
        if event.button() == Qt.MouseButton.MiddleButton or self.mode == "pan":
            self.drawing, self.pan_start = True, event.position().toPoint()
        elif p and self.mode in ("brush", "erase"):
            self.drawing, self.last_image_point = True, p
            self._stroke(p, p)
        elif p and self.mode == "polygon" and event.button() == Qt.MouseButton.LeftButton:
            self.poly.append(p)
            self.update()

    def mouseMoveEvent(self, event):
        p = self.image_point(event.position())
        if p:
            self.positionChanged.emit(*p)
        if not self.drawing:
            return
        if self.mode == "pan" or event.buttons() & Qt.MouseButton.MiddleButton:
            now = event.position().toPoint()
            self.offset += QPointF(now - self.pan_start)
            self.pan_start = now
            self.update()
        elif p and self.mode in ("brush", "erase"):
            self._stroke(self.last_image_point or p, p)
            self.last_image_point = p

    def mouseReleaseEvent(self, _event):
        if self.drawing and self.mode in ("brush", "erase"):
            self.maskChanged.emit()
        self.drawing = False

    def mouseDoubleClickEvent(self, _event):
        if self.mode == "polygon" and len(self.poly) >= 3 and self.mask is not None:
            cv2.fillPoly(self.mask, [np.array(self.poly, np.int32)], 255)
            self.poly.clear()
            self.maskChanged.emit()
            self.update()

    def _stroke(self, a: tuple[int, int], b: tuple[int, int]):
        if self.mask is None:
            return
        color = 0 if self.mode == "erase" else 255
        cv2.line(self.mask, a, b, color, self.brush, cv2.LINE_AA)
        cv2.circle(self.mask, b, max(1, self.brush // 2), color, -1, cv2.LINE_AA)
        self.update()


class DonorDialog(QDialog):
    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Donor patch transform")
        form = QFormLayout(self)
        self.values = {}
        defaults = {"source x": width // 3, "source y": height // 3, "width": 120, "height": 120,
                    "target x": width // 2, "target y": height // 2}
        for name, default in defaults.items():
            box = QSpinBox(); box.setRange(0, max(width, height)); box.setValue(default)
            self.values[name] = box; form.addRow(name.title(), box)
        self.angle = QDoubleSpinBox(); self.angle.setRange(-180, 180); form.addRow("Rotate degrees", self.angle)
        self.scale = QDoubleSpinBox(); self.scale.setRange(.1, 5); self.scale.setSingleStep(.05); self.scale.setValue(1); form.addRow("Scale", self.scale)
        self.poisson = QCheckBox("Use Poisson seamless clone"); self.poisson.setChecked(True); form.addRow(self.poisson)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)


class MainWindow(QMainWindow):
    def __init__(self, source: Path | None = None, mask: Path | None = None):
        super().__init__()
        self.setWindowTitle("Gothic Repair Suite — mask-first local repair")
        self.resize(1500, 980)
        self.project: RepairProject | None = None
        self.backends = discover_plugins(Path.cwd() / "plugins")
        self.canvas = Canvas()
        self.canvas.maskChanged.connect(self._mask_changed)
        self.canvas.positionChanged.connect(lambda x, y: self.statusBar().showMessage(f"x={x}, y={y}  zoom={self.canvas.zoom:.2f}x"))
        self._build_ui()
        if source and source.exists():
            self.open_source(source, mask)

    def _build_ui(self):
        bar = QToolBar("Tools"); self.addToolBar(bar)
        for label, mode in [("Brush", "brush"), ("Erase", "erase"), ("Polygon/Lasso", "polygon"), ("Pan", "pan")]:
            action = QAction(label, self); action.triggered.connect(lambda _=False, m=mode: setattr(self.canvas, "mode", m)); bar.addAction(action)
        bar.addSeparator()
        self.brush = QSpinBox(); self.brush.setRange(1, 300); self.brush.setValue(32); self.brush.valueChanged.connect(lambda v: setattr(self.canvas, "brush", v)); bar.addWidget(QLabel(" Brush px ")); bar.addWidget(self.brush)
        self.feather = QSpinBox(); self.feather.setRange(0, 100); self.feather.setValue(8); bar.addWidget(QLabel(" Feather px ")); bar.addWidget(self.feather)
        self.view = QComboBox(); self.view.addItems(["Working", "Original", "Candidate", "Mask overlay", "Difference", "Out-of-mask QA"]); self.view.currentTextChanged.connect(self.refresh); bar.addWidget(QLabel(" View ")); bar.addWidget(self.view)

        side = QWidget(); layout = QVBoxLayout(side)
        layout.addWidget(QLabel("Numbered defect checklist"))
        self.table = QTableWidget(5, 2); self.table.setHorizontalHeaderLabels(["Region", "Status"]); self.table.verticalHeader().hide(); self.table.cellClicked.connect(self._select_region); layout.addWidget(self.table)
        self.backend = QComboBox(); self.backend.addItems(sorted(self.backends)); layout.addWidget(QLabel("Repair backend")); layout.addWidget(self.backend)
        self.prompt = QComboBox(); self.prompt.setEditable(True); self.prompt.addItem("anatomically correct detailed feet and shins, crisp bas-relief, matching monochrome lighting"); layout.addWidget(QLabel("Backend prompt / note")); layout.addWidget(self.prompt)
        match_row = QHBoxLayout()
        self.contrast = QDoubleSpinBox(); self.contrast.setRange(.25, 3); self.contrast.setSingleStep(.05); self.contrast.setValue(1)
        self.grain = QDoubleSpinBox(); self.grain.setRange(0, 30); self.grain.setSingleStep(.25)
        match_row.addWidget(QLabel("Contrast")); match_row.addWidget(self.contrast); match_row.addWidget(QLabel("Grain")); match_row.addWidget(self.grain)
        layout.addLayout(match_row)
        for text, slot in [
            ("Generate inpaint candidate", self.generate_candidate),
            ("Donor patch / clone transform", self.donor_candidate),
            ("Approve candidate", self.approve), ("Reject candidate", self.reject),
            ("Undo", self.undo), ("Redo", self.redo),
            ("Save project", self.save_project), ("Load project", self.load_project),
            ("Export context crop", self.export_crop), ("Batch QA + final export", self.export_qa),
        ]:
            button = QPushButton(text); button.clicked.connect(slot); layout.addWidget(button)
        layout.addWidget(QLabel("Checkpoint history"))
        self.history_box = QComboBox(); self.history_box.activated.connect(self._goto_history); layout.addWidget(self.history_box)
        layout.addStretch()
        split = QSplitter(); split.addWidget(self.canvas); split.addWidget(side); split.setSizes([1200, 300]); self.setCentralWidget(split)

        menu = self.menuBar().addMenu("File")
        open_action = QAction("Open source…", self); open_action.triggered.connect(self.choose_source); menu.addAction(open_action)
        self._update_table()

    def choose_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open source image", "", "Images (*.png *.jpg *.tif *.tiff)")
        if path: self.open_source(Path(path), None)

    def open_source(self, source: Path, mask: Path | None):
        self.project = RepairProject.from_file(source)
        if mask and mask.exists():
            loaded = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
            self.project.set_mask(loaded)
        self._update_table(); self.refresh(); self.statusBar().showMessage(f"Loaded untouched source: {source.name}")

    def _select_region(self, row: int, _column: int):
        if self.project:
            self.project.active_region = row + 1; self.refresh()

    def _mask_changed(self):
        if self.project:
            self.project.set_mask(self.canvas.mask); self.refresh()

    def _update_table(self):
        names = ["Central feet & shins", "Reclining hip/legs", "Hooded cybernetic hand", "Floating arms", "Spear grip"]
        for row, name in enumerate(names):
            status = self.project.regions[row].status if self.project else "pending"
            self.table.setItem(row, 0, QTableWidgetItem(f"{row + 1}. {name}")); self.table.setItem(row, 1, QTableWidgetItem(status))
        self.table.resizeColumnsToContents()
        if self.project:
            self.history_box.blockSignals(True)
            self.history_box.clear(); self.history_box.addItems(self.project.history_labels)
            self.history_box.setCurrentIndex(self.project.history_index)
            self.history_box.blockSignals(False)

    def _goto_history(self, index: int):
        if self.project:
            self.project.goto_history(index); self.refresh()

    def refresh(self):
        if not self.project: return
        p, label = self.project, self.view.currentText()
        image = p.working
        if label == "Original": image = p.original
        elif label == "Candidate" and p.candidate is not None: image = p.candidate.image
        elif label == "Difference": image = cv2.convertScaleAbs(cv2.absdiff(p.original, p.working), alpha=4)
        elif label == "Out-of-mask QA": _, image = out_of_mask_diff(p.original, p.working, p.combined_approved_mask())
        self.canvas.overlay = label == "Mask overlay"
        self.canvas.set_data(image, p.region.mask)
        self._update_table()

    def generate_candidate(self):
        if not self.project or not np.any(self.project.region.mask):
            return self._error("Paint or load a mask first.")
        try:
            backend = self.backends[self.backend.currentText()]
            result = backend.inpaint(self.project.working, self.project.region.mask, self.prompt.currentText())
            result = match_luminance_and_grain(result, self.project.working, self.project.region.mask,
                                               self.contrast.value(), self.grain.value())
            soft = feather_mask(self.project.region.mask, self.feather.value())[..., None]
            blended = (result * soft + self.project.working * (1 - soft)).astype(np.uint8)
            self.project.set_candidate(blended, self.project.region.mask, "Mask-aware inpaint", backend.name,
                                       {"prompt": self.prompt.currentText(), "feather": self.feather.value()})
            self.view.setCurrentText("Candidate"); self.refresh()
        except Exception as exc: self._error(str(exc))

    def donor_candidate(self):
        if not self.project: return
        h, w = self.project.working.shape[:2]; dialog = DonorDialog(w, h, self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        v = {k: box.value() for k, box in dialog.values.items()}
        try:
            patch, patch_mask = transform_patch(self.project.working,
                (v["source x"], v["source y"], v["width"], v["height"]),
                (v["target x"], v["target y"]), dialog.angle.value(), dialog.scale.value())
            target_mask = cv2.bitwise_and(patch_mask, self.project.region.mask)
            if not np.any(target_mask): raise ValueError("Transformed donor does not overlap the active repair mask")
            if dialog.poisson.isChecked():
                ys, xs = np.where(target_mask > 0); center = (int(xs.mean()), int(ys.mean()))
                patch = cv2.seamlessClone(patch, self.project.working, target_mask, center, cv2.MIXED_CLONE)
            patch = match_luminance_and_grain(patch, self.project.working, target_mask,
                                              self.contrast.value(), self.grain.value())
            self.project.set_candidate(patch, target_mask, "Donor patch", "manual-clone",
                                       {"angle": dialog.angle.value(), "scale": dialog.scale.value(), "poisson": dialog.poisson.isChecked()})
            self.view.setCurrentText("Candidate"); self.refresh()
        except Exception as exc: self._error(str(exc))

    def approve(self):
        if not self.project or not self.project.candidate: return self._error("Generate a candidate first.")
        try: self.project.approve_candidate(); self.view.setCurrentText("Working"); self.refresh()
        except Exception as exc: self._error(str(exc))

    def reject(self):
        if self.project: self.project.reject_candidate(); self.view.setCurrentText("Working"); self.refresh()

    def undo(self):
        if self.project: self.project.undo(); self.refresh()

    def redo(self):
        if self.project: self.project.redo(); self.refresh()

    def save_project(self):
        if not self.project: return
        folder = QFileDialog.getExistingDirectory(self, "Select project folder")
        if folder: self.project.save(Path(folder) / "Pass7_Repair_Project.grsproj")

    def load_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Open .grsproj project folder")
        if folder:
            try: self.project = RepairProject.load(folder); self.refresh()
            except Exception as exc: self._error(str(exc))

    def export_crop(self):
        if not self.project or not np.any(self.project.region.mask): return self._error("Active region has no mask.")
        ys, xs = np.where(self.project.region.mask > 0); pad = 180
        x0, x1 = max(0, xs.min() - pad), min(self.project.working.shape[1], xs.max() + pad)
        y0, y1 = max(0, ys.min() - pad), min(self.project.working.shape[0], ys.max() + pad)
        path, _ = QFileDialog.getSaveFileName(self, "Save repair context crop", f"region_{self.project.active_region}_context.png", "PNG (*.png)")
        if path: cv2.imwrite(path, self.project.working[y0:y1, x0:x1])

    def export_qa(self):
        if not self.project: return
        size, ok = QInputDialog.getInt(self, "Export size", "Square pixels", 2048, 256, 16384, 1)
        if not ok: return
        folder = QFileDialog.getExistingDirectory(self, "Select QA export folder")
        if folder:
            try:
                make_qa_bundle(self.project, Path(folder), size)
                QMessageBox.information(self, "Export complete", f"QA bundle saved to {folder}\nOut-of-mask invariant: PASS")
            except Exception as exc: self._error(str(exc))

    def _error(self, message: str): QMessageBox.warning(self, "Gothic Repair Suite", message)


def run(source: Path | None = None, mask: Path | None = None):
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow(source, mask); window.show()
    return app.exec()
