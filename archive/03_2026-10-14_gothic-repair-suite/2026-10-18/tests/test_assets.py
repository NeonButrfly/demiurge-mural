from pathlib import Path

import cv2
import numpy as np

from gothic_repair.core import RepairProject


ROOT = Path(__file__).parents[1]


def test_pass7_assets_align_and_mask_preloads():
    source = ROOT / "assets" / "Gothic_Relief_Pass_7_Original.png"
    mask_path = ROOT / "assets" / "Pass7_Central_Legs_Inpaint_Mask.png"
    preview = ROOT / "assets" / "Pass7_Masked_Area_Preview.png"
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    shown = cv2.imread(str(preview), cv2.IMREAD_COLOR)
    assert image.shape == shown.shape == (1254, 1254, 3)
    assert mask.shape == image.shape[:2]
    assert 1000 < np.count_nonzero(mask) < image.shape[0] * image.shape[1] // 10
    project = RepairProject.from_file(source); project.set_mask(mask)
    assert np.array_equal(project.original, image)
    assert np.array_equal(project.region.mask > 0, mask > 0)


def test_additional_repair_masks_are_local_and_aligned():
    source = cv2.imread(str(ROOT / "assets" / "Gothic_Relief_Pass_7_Original.png"))
    expected = {
        "Pass7_Hooded_Cybernetic_Hand_Mask.png": (4000, 7000),
        "Pass7_Spear_Grip_Mask.png": (1500, 4000),
        "Pass7_Reclining_Hip_Legs_Mask.png": (18000, 23000),
        "Pass7_Ownerless_Center_Arm_Mask.png": (9000, 12000),
        "Pass7_Central_Bulbous_Forms_Mask.png": (5500, 7500),
        "Pass7_RobeExtrusion_Mask.png": (3000, 4000),
        "Pass7_UpperExtrusion_Mask.png": (1500, 2500),
        "Pass7_Highlighted_Unwanted_Arm_Mask.png": (4000, 6000),
    }
    for name, (minimum, maximum) in expected.items():
        mask = cv2.imread(str(ROOT / "assets" / name), cv2.IMREAD_GRAYSCALE)
        assert mask.shape == source.shape[:2]
        assert minimum < np.count_nonzero(mask) < maximum


def test_v7_restoration_sources_are_full_resolution_and_neutral_reference():
    reference = cv2.imread(
        str(ROOT / "assets" / "references" / "Demiurge_Four_Panel_Restoration_Reference_2048.png"),
        cv2.IMREAD_UNCHANGED,
    )
    generated = cv2.imread(
        str(ROOT / "assets" / "generated" / "Pass7_Anatomy_Cybernetic_Restoration_v7_API.png"),
        cv2.IMREAD_COLOR,
    )
    assert reference.shape == (2048, 2048)
    assert generated.shape == (2048, 2048, 3)


def test_v8_original_halo_restore_is_strictly_masked():
    target = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cybernetic_Restoration_v7.png"),
        cv2.IMREAD_COLOR,
    )
    restored = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos.png"),
        cv2.IMREAD_COLOR,
    )
    selection = cv2.imread(
        str(ROOT / "assets" / "Pass7_Original_Halos_Selection.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert target.shape == restored.shape == (2048, 2048, 3)
    assert selection.shape == (2048, 2048)
    changed = np.any(target != restored, axis=2)
    assert np.count_nonzero(changed) > 0
    assert np.count_nonzero(changed & (selection == 0)) == 0
    selected = selection > 0
    assert np.array_equal(restored[:, :, 0][selected], restored[:, :, 1][selected])
    assert np.array_equal(restored[:, :, 1][selected], restored[:, :, 2][selected])


def test_v6_source_halo_pass1_changes_only_halo_selection():
    destination = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v6.png"), cv2.IMREAD_COLOR
    )
    restored = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png"),
        cv2.IMREAD_COLOR,
    )
    selection = cv2.imread(
        str(ROOT / "assets" / "Pass7_v6_Source_Halos_Selection.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert destination.shape == restored.shape == (1254, 1254, 3)
    changed = np.any(destination != restored, axis=2)
    assert np.count_nonzero(changed) > 0
    assert np.count_nonzero(changed & (selection == 0)) == 0
    selected = selection > 0
    assert np.array_equal(restored[:, :, 0][selected], restored[:, :, 1][selected])
    assert np.array_equal(restored[:, :, 1][selected], restored[:, :, 2][selected])


def test_v7_pdf_repairs_change_only_registered_annotation_masks():
    destination = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png"),
        cv2.IMREAD_COLOR,
    )
    repaired = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"),
        cv2.IMREAD_COLOR,
    )
    union = cv2.imread(
        str(ROOT / "assets" / "Pass7_PDF_Annotated_Union_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    red = cv2.imread(
        str(ROOT / "assets" / "Pass7_PDF_Red_Replacement_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    yellow = cv2.imread(
        str(ROOT / "assets" / "Pass7_PDF_Yellow_Anatomy_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert destination.shape == repaired.shape == (1254, 1254, 3)
    assert union.shape == red.shape == yellow.shape == (1254, 1254)
    assert np.array_equal(union > 0, (red > 0) | (yellow > 0))
    changed = np.any(destination != repaired, axis=2)
    assert np.count_nonzero(changed) > 100_000
    assert np.count_nonzero(changed & (union == 0)) == 0
    selected = union > 0
    assert np.array_equal(repaired[:, :, 0][selected], repaired[:, :, 1][selected])
    assert np.array_equal(repaired[:, :, 1][selected], repaired[:, :, 2][selected])


def test_v8_cybernetic_reintegration_preserves_unselected_anatomy():
    destination = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"),
        cv2.IMREAD_COLOR,
    )
    final = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration.png"),
        cv2.IMREAD_COLOR,
    )
    union = cv2.imread(
        str(ROOT / "assets" / "Pass7_v8_Cybernetic_Reintegration_Union_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert destination.shape == final.shape == (1254, 1254, 3)
    assert union.shape == (1254, 1254)
    changed = np.any(destination != final, axis=2)
    assert 80_000 < np.count_nonzero(changed) < 90_000
    assert np.count_nonzero(changed & (union == 0)) == 0
    selected = union > 0
    assert np.array_equal(final[:, :, 0][selected], final[:, :, 1][selected])
    assert np.array_equal(final[:, :, 1][selected], final[:, :, 2][selected])


def test_v8_masks_have_expected_local_scopes():
    expected = {
        "Pass7_v8_Demon_Claw_Mask.png": (5_000, 6_500),
        "Pass7_v8_Reclining_Human_Mask.png": (49_000, 52_000),
        "Pass7_v8_Hooded_Arm_Mask.png": (7_500, 9_000),
        "Pass7_v8_Surface_Filigree_Mask.png": (21_000, 25_000),
    }
    for name, (minimum, maximum) in expected.items():
        mask = cv2.imread(str(ROOT / "assets" / name), cv2.IMREAD_GRAYSCALE)
        assert mask.shape == (1254, 1254)
        assert minimum < np.count_nonzero(mask) < maximum


def test_v9_reviewed_corrections_are_strictly_masked_and_neutral():
    destination = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png"),
        cv2.IMREAD_COLOR,
    )
    final = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections.png"),
        cv2.IMREAD_COLOR,
    )
    union = cv2.imread(
        str(ROOT / "assets" / "Pass7_v9_Review_Corrections_Union_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert destination.shape == final.shape == (1254, 1254, 3)
    assert union.shape == (1254, 1254)
    assert 205_000 < np.count_nonzero(union) < 215_000
    changed = np.any(destination != final, axis=2)
    assert 198_000 < np.count_nonzero(changed) < 208_000
    assert np.count_nonzero(changed & (union == 0)) == 0
    assert np.array_equal(final[:, :, 0][changed], final[:, :, 1][changed])
    assert np.array_equal(final[:, :, 1][changed], final[:, :, 2][changed])


def test_v10_anatomy_halo_corrections_are_strictly_masked_and_neutral():
    destination = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections.png"),
        cv2.IMREAD_COLOR,
    )
    final = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections.png"),
        cv2.IMREAD_COLOR,
    )
    union = cv2.imread(
        str(ROOT / "assets" / "Pass7_v10_Anatomy_Halo_Union_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert destination.shape == final.shape == (1254, 1254, 3)
    assert union.shape == (1254, 1254)
    assert 120_000 < np.count_nonzero(union) < 125_000
    changed = np.any(destination != final, axis=2)
    assert 118_000 < np.count_nonzero(changed) < 123_000
    assert np.count_nonzero(changed & (union == 0)) == 0
    assert np.array_equal(final[:, :, 0][changed], final[:, :, 1][changed])
    assert np.array_equal(final[:, :, 1][changed], final[:, :, 2][changed])


def test_v11_erased_region_fills_are_masked_neutral_and_remove_yellow():
    destination = cv2.imread(
        str(ROOT / "assets" / "reviews" / "Pass7_v10_User_Erased_Areas.png"),
        cv2.IMREAD_COLOR,
    )
    final = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png"),
        cv2.IMREAD_COLOR,
    )
    union = cv2.imread(
        str(ROOT / "assets" / "Pass7_v11_Erased_Regions_Union_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    assert destination.shape == final.shape == (1131, 1131, 3)
    assert union.shape == (1131, 1131)
    assert 55_000 < np.count_nonzero(union) < 59_000
    changed = np.any(destination != final, axis=2)
    assert 55_000 < np.count_nonzero(changed) < 59_000
    assert np.count_nonzero(changed & (union == 0)) == 0
    assert np.array_equal(final[:, :, 0][changed], final[:, :, 1][changed])
    assert np.array_equal(final[:, :, 1][changed], final[:, :, 2][changed])
    hsv = cv2.cvtColor(final, cv2.COLOR_BGR2HSV)
    yellow = (hsv[:, :, 0] >= 16) & (hsv[:, :, 0] <= 42) & (hsv[:, :, 1] > 55)
    assert np.count_nonzero(yellow & (union > 0)) == 0


def test_v12_copper_filigree_is_overlay_only_and_preserves_v11_elsewhere():
    base = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png"),
        cv2.IMREAD_COLOR,
    )
    final = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree.png"),
        cv2.IMREAD_COLOR,
    )
    mask = cv2.imread(
        str(ROOT / "assets" / "Pass7_v12_Copper_Cybernetic_Detail_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    overlay = cv2.imread(
        str(ROOT / "assets" / "generated" / "Pass7_v12_Copper_Cybernetic_Overlay.png"),
        cv2.IMREAD_UNCHANGED,
    )
    assert base.shape == final.shape == (1131, 1131, 3)
    assert mask.shape == (1131, 1131)
    assert overlay.shape == (1131, 1131, 4)
    changed = np.any(base != final, axis=2)
    assert 50_000 < np.count_nonzero(changed) < 60_000
    assert np.count_nonzero(changed & (mask == 0)) == 0
    assert np.array_equal(mask > 0, overlay[:, :, 3] > 0)
    hsv = cv2.cvtColor(final, cv2.COLOR_BGR2HSV)
    copper = changed & (hsv[:, :, 0] >= 3) & (hsv[:, :, 0] <= 26) & (hsv[:, :, 1] >= 55)
    assert np.count_nonzero(copper) > 30_000


def test_v13_contains_actual_masked_cybernetic_hardware():
    base = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png"),
        cv2.IMREAD_COLOR,
    )
    final = cv2.imread(
        str(ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics.png"),
        cv2.IMREAD_COLOR,
    )
    mask = cv2.imread(
        str(ROOT / "assets" / "Pass7_v13_Actual_Copper_Cybernetics_Mask.png"),
        cv2.IMREAD_GRAYSCALE,
    )
    overlay = cv2.imread(
        str(ROOT / "assets" / "generated" / "Pass7_v13_Actual_Copper_Cybernetics_Overlay.png"),
        cv2.IMREAD_UNCHANGED,
    )
    assert base.shape == final.shape == (1131, 1131, 3)
    assert mask.shape == (1131, 1131)
    assert overlay.shape == (1131, 1131, 4)
    changed = np.any(base != final, axis=2)
    assert 40_000 < np.count_nonzero(changed) < 48_000
    assert np.count_nonzero(changed & (mask == 0)) == 0
    assert np.array_equal(mask > 0, overlay[:, :, 3] > 0)
    hsv = cv2.cvtColor(final, cv2.COLOR_BGR2HSV)
    copper = changed & (hsv[:, :, 0] >= 3) & (hsv[:, :, 0] <= 27) & (hsv[:, :, 1] >= 55)
    assert np.count_nonzero(copper) > 35_000

