# Demiurge Mural

Four-panel grayscale artwork prepared from the supplied 2048 × 2048 source for relief or heightmap workflows.

Tracked request: [Issue #1](https://github.com/NeonButrfly/demiurge-mural/issues/1)

## Deliverables

- `assets/source/demiurge_full_four_panel_source_2048x2048_grayscale.png` — source copy, unchanged.
- `outputs/panels/` — four 1024 × 1024 grayscale panel images. Each maps to a 400 × 400 mm panel at 2.56 px/mm, with a 5 mm low-Z border and a 390 × 390 mm artwork interior.
- `outputs/single/demiurge_single_800mm_grayscale.png` — one continuous 800 × 800 mm grayscale image with only an outer 5 mm low-Z border.
- `outputs/single/demiurge_single_800mm_architecture_depth_enhanced_grayscale.png` — non-destructive variant with stronger side-architecture and circular-element depth cues.
- `outputs/single/demiurge_single_800mm_depthcarve_blended_grayscale.png` — depth-map-blended variant using the tracked DepthCarve reference.
- `assets/references/depthcarve-depth-map-8bit_1.png` — supplied 8-bit depth-map input.
- `outputs/previews/demiurge_four_panel_combined_preview.png` — assembled visual check of the four panels.

The panel images are geometry/layout artwork inputs. Their grayscale values encode the relief signal; the dark perimeter is intentionally low-Z. Physical printer fit and relief depth are not established until the target slicer and printer are checked.
