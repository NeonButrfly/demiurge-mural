import json

import cv2
import numpy as np

from gothic_repair.backends import OpenCVBackend
from gothic_repair.core import RepairProject, out_of_mask_diff, strict_alpha_composite, strict_composite
from gothic_repair.qa import make_qa_bundle


def fixture_image(size=96):
    y, x = np.mgrid[:size, :size]
    gray = ((x * 2 + y) % 255).astype(np.uint8)
    return cv2.merge([gray, gray, gray])


def fixture_mask(size=96):
    mask = np.zeros((size, size), np.uint8)
    cv2.circle(mask, (size // 2, size // 2), 12, 255, -1)
    return mask


def test_strict_composite_preserves_every_outside_byte():
    original = fixture_image()
    candidate = np.full_like(original, 231)
    mask = fixture_mask()
    result = strict_composite(original, candidate, mask)
    assert np.array_equal(result[mask == 0], original[mask == 0])
    assert np.all(result[mask > 0] == 231)
    count, _ = out_of_mask_diff(original, result, mask)
    assert count == 0


def test_strict_alpha_composite_feathers_only_inside_mask():
    original = fixture_image()
    candidate = np.full_like(original, 231)
    mask = fixture_mask()
    mask = cv2.GaussianBlur(mask, (9, 9), 2)
    result = strict_alpha_composite(original, candidate, mask)
    assert np.array_equal(result[mask == 0], original[mask == 0])
    assert np.any(result[mask > 0] != original[mask > 0])
    count, _ = out_of_mask_diff(original, result, mask)
    assert count == 0


def test_round_trip_persistence(tmp_path):
    project = RepairProject(fixture_image(), "fixture.png")
    mask = fixture_mask(); project.set_mask(mask)
    project.set_candidate(np.full_like(project.working, 100), mask, "test", "test")
    project.approve_candidate()
    loaded = RepairProject.load(project.save(tmp_path / "saved.grsproj"))
    assert loaded.original_sha256 == project.original_sha256
    assert np.array_equal(loaded.working, project.working)
    assert np.array_equal(loaded.regions[0].mask, mask)
    assert loaded.regions[0].status == "approved"
    assert loaded.assert_invariant() == 0


def test_undo_redo_restores_exact_pixels():
    project = RepairProject(fixture_image())
    original = project.working.copy(); mask = fixture_mask()
    candidate = original.copy(); candidate[mask > 0] = (9, 9, 9)
    project.set_candidate(candidate, mask, "dark patch", "test"); project.approve_candidate()
    changed = project.working.copy()
    assert project.undo() and np.array_equal(project.working, original)
    assert project.redo() and np.array_equal(project.working, changed)
    assert project.goto_history(0) and np.array_equal(project.working, original)


def test_local_inpaint_is_mask_aware_and_export_bundle_passes(tmp_path):
    image = fixture_image(); mask = fixture_mask()
    damaged = image.copy(); damaged[mask > 0] = 255
    project = RepairProject(damaged); project.set_mask(mask)
    repaired = OpenCVBackend().inpaint(damaged, mask, radius=3)
    project.set_candidate(repaired, mask, "local inpaint", "opencv"); project.approve_candidate()
    folder = make_qa_bundle(project, tmp_path / "qa", 256)
    report = json.loads((folder / "QA_REPORT.json").read_text())
    assert report["strict_invariant_passed"] is True
    assert cv2.imread(str(folder / "06_final_256x256.png")).shape[:2] == (256, 256)
    assert (folder / "07_heightmap_draft_256x256.png").exists()

