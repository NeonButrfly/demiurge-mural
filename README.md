# Demiurge Mural

Four-panel grayscale artwork prepared from the supplied 2048 × 2048 source for relief or heightmap workflows.

Tracked request: [Issue #1](https://github.com/NeonButrfly/demiurge-mural/issues/1)

## Deliverables

- `assets/source/demiurge_full_four_panel_source_2048x2048_grayscale.png` — source copy, unchanged.
- `outputs/panels/` — four 1024 × 1024 grayscale panel images. Each maps to a 400 × 400 mm panel at 2.56 px/mm, with a 5 mm low-Z border and a 390 × 390 mm artwork interior.
- `outputs/single/demiurge_single_800mm_grayscale.png` — one continuous 800 × 800 mm grayscale image with only an outer 5 mm low-Z border.
- `outputs/single/demiurge_single_800mm_architecture_depth_enhanced_grayscale.png` — non-destructive variant with stronger side-architecture and circular-element depth cues.
- `outputs/single/demiurge_single_800mm_circular_regions_restored_grayscale.png` — restoration variant returning the star circle, eclipse circle, and their surrounding architecture to the original grayscale baseline while preserving the rest of the enhanced image.
- `outputs/single/demiurge_single_800mm_depthcarve_blended_grayscale.png` — depth-map-blended variant using the tracked DepthCarve reference.
- `assets/references/depthcarve-depth-map-8bit_1.png` — supplied 8-bit depth-map input.
- `outputs/relief/` — four binary STL bas-relief panels and a generation manifest. Each panel is 400 × 400 mm; together they form 800 × 800 mm, with a calibrated maximum height of 25.1175 mm.
- `outputs/relief_restored/` — four regenerated 400 × 400 mm STL panels based on the circular-region restoration variant.
- `outputs/relief_250_restored/` — geometry-preserving restoration outputs based directly on the supplied 250 × 250 mm Desktop STLs; panels 3 and 4 are byte-identical copies.
- `scripts/validate_bas_relief.py` — binary-STL bounds and closed-manifold validation.
- `assets/references/panel_1_upper_left_example.stl` — supplied example STL used to calibrate the depth scale.
- `outputs/previews/demiurge_four_panel_combined_preview.png` — assembled visual check of the four panels.
- `scripts/restore_circular_regions.py` — deterministic restoration and regenerated-panel workflow for issue #7.
- `scripts/restore_250mm_panel_circles.py` — local-Z-only restoration workflow for issue #8; it preserves the supplied 250 mm XY geometry and topology.

The panel images are geometry/layout artwork inputs. Their grayscale values encode the relief signal; the dark perimeter is intentionally low-Z. Physical printer fit and relief depth are not established until the target slicer and printer are checked.
