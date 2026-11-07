# Gothic Repair Suite

A complete local, mask-first desktop workstation for targeted repair of dense monochrome artwork. It ships preloaded with the supplied Pass 7 source and central-legs mask, preserves the source untouched, and refuses final QA export if a working-resolution pixel changed outside approved masks.

Tracking: [GitHub issue #1](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/1), milestone `Local Image Repair Suite v1`.

## Start on Windows

Double-click `launch_windows.bat`. The first launch creates a private `.venv` and installs the dependencies; later launches open directly. Python 3.10 or newer is required.

Manual alternative:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\python.exe -m gothic_repair.app
```

## Continue on macOS

The portable handoff opens the current 2048×2048 continuation image rather than the older bundled Pass 7 original:

```bash
chmod +x setup_mac.sh launch_mac.sh run_tests_mac.sh
./setup_mac.sh
./launch_mac.sh
```

See `MAC_CONTINUATION.md` for the current-image hash, Git-history restoration, testing, backend configuration, and the safe masked-repair workflow. Build a verified transfer ZIP with:

```bash
.venv/bin/python scripts/build_mac_continuation_bundle.py
```

## Practical workflow

1. Select a numbered defect region. Region 1 starts with `Pass7_Central_Legs_Inpaint_Mask.png`.
2. Inspect at any zoom. The canvas uses image coordinates for painting, and at 1× or higher displays without interpolation for pixel inspection. Mouse wheel zooms around the cursor; middle-drag or Pan moves the canvas.
3. Refine the mask with Brush, Erase, or Polygon/Lasso (double-click closes the polygon). Set brush and feather sizes in image pixels.
4. Generate a local mask-aware candidate using OpenCV Telea inpainting, or use Donor patch to move/rotate/scale a source rectangle and optionally Poisson-blend it.
5. Use Candidate, Original, Working, Difference, Mask overlay, and Out-of-mask QA views. Approve only a candidate that holds up at high zoom; Reject leaves the working image untouched.
6. Save a `.grsproj` folder for a complete round-trip project, or export a context crop for use with a stronger configured backend.
7. Batch QA export writes before/after, mask overlay, absolute difference, out-of-mask violation visualization, final resized PNG, luminance heightmap draft, and `QA_REPORT.json`.

## Repair backends

- **OpenCV local:** installed and functional; mask-aware Telea/NS content propagation. Useful for small seams and texture cleanup, but not a generative anatomy model. It should not be expected to invent convincing toes by itself.
- **Remote endpoint:** set `GOTHIC_REPAIR_ENDPOINT` and optional `GOTHIC_REPAIR_TOKEN`. The endpoint receives multipart `image`, `mask`, `prompt`, and JSON `options`; it may return PNG bytes or JSON containing `image_base64`.
- **Local model plugin:** copy `plugins/example_backend.py.example` to a `.py` file and expose an `InpaintBackend` instance as `BACKEND`. This is the integration point for a locally installed mask-aware diffusion model such as ComfyUI or another provider.

Only Python plugin files you trust should be placed in `plugins/`; they execute locally during discovery.

## Guarantees and boundaries

- The original PNG in `assets/` is never overwritten by the app.
- Candidate approval copies candidate pixels only where its binary approved mask is nonzero.
- QA computes the union of approved masks and asserts zero changed pixels outside it before final export.
- Feathering, luminance/contrast normalization, deterministic grain matching, donor transforms, and Poisson blending are implemented.
- Project history supports checkpointed undo/redo and persists exactly in a `.grsproj` directory.
- The optional heightmap is a grayscale draft for later relief work, not validated physical geometry.
- Rotation and scale transforms are implemented for donor patches. Free-form mesh warp is not included in v1; a plugin can provide it.
- Final resizing necessarily interpolates the exported copy. The byte-identity guarantee applies to the full-resolution working image before resize, which is also included in QA as `02_after.png`.

## Tests

Run `run_tests_windows.bat`, or:

```powershell
.venv\Scripts\python.exe -m pytest
```

The suite checks strict out-of-mask compositing, project persistence, undo/redo, real local inpainting, export/heightmap creation, supplied-asset alignment, mask preload, and headless desktop startup.

## Asset integrity

All three supplied files remain separate and unchanged in `assets/`. Their SHA-256 values are recorded in `assets/SHA256SUMS.txt` and verified by the test/validation workflow.

## Pass 7 repaired output

`outputs/Pass7_Anatomy_Cleanup_v3.png` is the cumulative mask-only repair. It includes the central feet/shins, hooded cybernetic hand, spear grip, and reclining hip/legs corrections. `Pass7_Anatomy_Cleanup_v3_QA.json` records the approved-mask union and the zero out-of-mask-change assertion. Regenerate the final pass with:

```powershell
.venv\Scripts\python.exe scripts\prepare_full_anatomy_cleanup.py
.venv\Scripts\python.exe scripts\build_manual_anatomy_candidate.py
.venv\Scripts\python.exe scripts\composite_full_anatomy_cleanup.py
```

The corrected center pass is `outputs/Pass7_Anatomy_Cleanup_v4.png`. It additionally removes the ownerless distended center arm/hand and the adjoining unexplained rounded forms, replacing them with non-anatomical feather/drapery relief. Regenerate it after v3 with:

```powershell
.venv\Scripts\python.exe scripts\prepare_center_cleanup.py
.venv\Scripts\python.exe scripts\build_center_cleanup_candidates.py
.venv\Scripts\python.exe scripts\composite_center_cleanup.py
```

`outputs/Pass7_Anatomy_Cleanup_v5.png` additionally repairs the two robe protrusions marked red in the user's supplied annotation. Regenerate v5 after v4 with:

```powershell
.venv\Scripts\python.exe scripts\prepare_highlighted_extrusions.py
.venv\Scripts\python.exe scripts\build_highlighted_extrusion_candidate.py
.venv\Scripts\python.exe scripts\composite_highlighted_extrusions.py
```

`outputs/Pass7_Anatomy_Cleanup_v6.png` removes the unwanted forearm and hand marked red in the user's v5 annotation, replacing only that selected footprint with continuous monochrome robe folds. Regenerate v6 after v5 with:

```powershell
.venv\Scripts\python.exe scripts\prepare_highlighted_arm_removal.py
.venv\Scripts\python.exe scripts\build_highlighted_arm_candidate.py
.venv\Scripts\python.exe scripts\composite_highlighted_arm_removal.py
```

`outputs/Pass7_Anatomy_Cybernetic_Restoration_v7.png` is the 2048×2048 reference-guided restoration of halos, classical adult sculptural anatomy, cybernetic plates/ports, and body-attached cables. Unlike v1–v6's local repairs, v7 is an intentional whole-image generative edit, so the mask-only byte-identity guarantee does not apply to this pass. The untouched v6 remains available. Finalize the persisted API edit with:

```powershell
.venv\Scripts\python.exe scripts\finalize_cybernetic_restoration.py
```

`outputs/Pass7_Anatomy_Cybernetic_Restoration_v8_Original_Halos.png` is retained only as the rejected first interpretation of the halo request. It used the wrong reference and destination and is superseded by the source-accurate pass below.

`outputs/Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png` is the corrected first halo pass. It uses the supplied 2048 Demiurge artwork as the donor source and `Pass7_Anatomy_Cleanup_v6.png` as the destination. The source's upper mechanical ring and lower radial sunburst crown are transferred deterministically; all destination pixels outside the two halo selections remain byte-identical. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\prepare_source_halo_transfer.py
.venv\Scripts\python.exe scripts\build_source_halo_donor.py
.venv\Scripts\python.exe scripts\finalize_source_halo_pass1.py
```

`outputs/Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png` applies the red and yellow corrections drawn in `10152026.pdf` to the halo-pass destination. Red regions receive focused replacement donors for the horned head, five-finger spear grip, and lower reclining armored figure. Yellow regions are converted into locally harmonized drapery, feather, armor, cable, and skull relief. The registered PDF masks are the complete allowed-change area; QA confirms zero changed pixels outside them. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\prepare_pdf_anatomy_annotations.py
.venv\Scripts\python.exe scripts\composite_pdf_annotated_repairs.py
```

`outputs/Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration.png` replaces the overly dark armored reclining donor with a grayscale human figure, clarifies the upper-right demon claw, preserves and re-engraves the hooded figure's cybernetic arm, and adds restrained surface filigree to five existing bodies. The 2048 Demiurge source is a motif reference; v7 remains the anatomical and compositional destination. Rebuild and reproduce its masks with:

```powershell
.venv\Scripts\python.exe scripts\prepare_cybernetic_reintegration.py
.venv\Scripts\python.exe scripts\composite_cybernetic_reintegration.py
```

The v8 QA report asserts that all pixels outside `Pass7_v8_Cybernetic_Reintegration_Union_Mask.png` remain byte-identical. A separate completion analysis is packaged with the final raster, masks, donors, difference view, and out-of-mask visualization.

The user rejected portions of v8 after a color-marked review. `outputs/Pass7_Anatomy_Cleanup_v9_Reviewed_Corrections.png` supersedes it. V9 returns to the accepted v7 destination, rebuilds the yellow demon claw/wing junction, replaces the blue/green lower-right graft with one draped silver relief figure, restores the clean v7 hooded cybernetic arm, and uses the user's externally repaired six-panel donor sheet to remove the red ownerless bulbs. Issue [#12](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/12) and `docs/prompts/reviewed-reintegration-corrections.md` capture the review requirements. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\prepare_v9_review_corrections.py
.venv\Scripts\python.exe scripts\composite_v9_review_corrections.py
```

The v9 QA report confirms a 1254×1254 output, neutral grayscale for every changed pixel, and zero changed pixels outside `Pass7_v9_Review_Corrections_Union_Mask.png`. Its delivery archive includes the final raster, mask preview, separate masks, accepted donors, difference image, detail montage, out-of-mask visualization, and QA report.

`outputs/Pass7_Anatomy_Cleanup_v10_Anatomy_Halo_Corrections.png` supersedes v9 for issue [#13](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/13). It replaces the upper demon's malformed arm with one attached five-talon limb, rebuilds the lower-right reclining figure as one fully draped body, centers the original-source spiked halo on the front angel, replaces the ownerless central protrusion with continuous robe and feather folds, and removes the two upper-right bubble clusters. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\prepare_v10_anatomy_halo_corrections.py
.venv\Scripts\python.exe scripts\composite_v10_anatomy_halo_corrections.py
```

The v10 QA report verifies a 1254×1254 neutral-grayscale result and zero changed pixels outside `Pass7_v10_Anatomy_Halo_Union_Mask.png`. The deliverables archive contains the final raster, separate masks, mask preview, accepted donors, difference image, detail montage, out-of-mask visualization, analysis, and QA JSON.

The user rejected v10 and supplied an 1131×1131 review image with two translucent-yellow replacement regions. `outputs/Pass7_Anatomy_Cleanup_v11_Erased_Areas_Filled.png` fills only those two regions: a complete demon head/neck/shoulder/arm/claw reconstruction and one fully draped lower-right reclining figure. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\prepare_v11_erased_region_fills.py
.venv\Scripts\python.exe scripts\composite_v11_erased_region_fills.py
```

`docs/prompts/v11-erased-region-fill-prompts.md` contains the same two prompts for external inpainting tools. V11 remains a review candidate until the user accepts the anatomy; its automated QA only establishes mask confinement, dimensions, yellow-paint removal, and neutral grayscale.

`outputs/Pass7_Anatomy_Cleanup_v12_Copper_Cybernetic_Filigree.png` adds a separate copper cybernetic-detail layer over v11 for issue [#14](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/14). The supplied 2048 copper artwork is used only to derive the copper palette and mechanical vocabulary. It is never used as a replacement image or donor. The v11 figures, anatomy, composition, and monochrome relief remain the destination; copper is confined to a transparent overlay of halo metalwork, demon harness and wing ribs, hooded arm hardware, skull/feather machinery, spear fittings, and selected garment filigree. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\build_v12_copper_cybernetic_filigree.py
```

The v12 QA report verifies the 1131×1131 dimensions, records source/reference/final hashes, and asserts zero changed pixels outside `Pass7_v12_Copper_Cybernetic_Detail_Mask.png`. The transparent BGRA overlay is also exported separately so its intensity can be adjusted without regenerating or replacing the underlying artwork. V12 remains a visual-review candidate until the user accepts the copper placement and density.

V12 was rejected because its copper treatment read as outlining rather than cybernetics. `outputs/Pass7_Anatomy_Cleanup_v13_Actual_Copper_Cybernetics.png` supersedes it with solid fitted plates, bolted interface ports, joint collars, connected conduits, a segmented hooded gauntlet, demon harness/wing-root hardware, and a mechanical spear clamp. It starts again from v11, not v12, so none of the rejected outline treatment is inherited. Rebuild with:

```powershell
.venv\Scripts\python.exe scripts\build_v13_actual_cybernetics.py
```

The v13 overlay and mask remain separate from the v11 raster. Its QA report asserts zero changed pixels outside the hardware overlay, and `docs/prompts/v13-actual-cybernetics.md` records the user correction and artistic-validation boundary.
