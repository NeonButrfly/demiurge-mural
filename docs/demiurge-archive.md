# Demiurge archive and chronology

This archive consolidates the merged `demiurge-collect` collection and the other Demiurge project/task locations found in the user project areas. Its dated groups run from the earliest material toward the latest. Original filenames and bytes are preserved; the manifest records each file's source path, source modification time, size, SHA-256, and archive path.

The archive currently contains **1,081 files totaling 5,625,696,848 bytes**. Binary media and model files use Git LFS. See [the complete SHA-256 manifest](../archive/manifest.csv).

## Chronological hierarchy

1. [`archive/00_legacy-model-folder/`](../archive/00_legacy-model-folder/) — 14 early model-folder files from 2026-09-09 through 2026-10-13.
2. [`archive/01_2026-09-18_to_10-20_collect-nested/`](../archive/01_2026-09-18_to_10-20_collect-nested/) — 102 files from the earlier nested `demiurge` folder inside the merged collection, including early relief models, maps, references, and the continuation bundle.
3. [`archive/02_2026-10-06_hueforge/`](../archive/02_2026-10-06_hueforge/) — four HueForge project/model files, including the `.hfp`, `.hfpt`, STL, and description.
4. [`archive/03_2026-10-14_gothic-repair-suite/`](../archive/03_2026-10-14_gothic-repair-suite/) — 438 project files from the Gothic Repair Suite task folder, including code, docs, assets, masks, and outputs. Its GitHub history is available in the [source repository](https://github.com/NeonButrfly/gothic-image-repair-suite) at source commit `a1bad6d9a714c65a057afc6f0c9b3ea2adc46c58`.
5. [`archive/04_2026-10-20_repair-task/`](../archive/04_2026-10-20_repair-task/) — 349 files from the later repair task, including scripts, work inputs, grayscale and relief candidates, X2D packages, and two Demiurge images formerly in Downloads.
6. [`archive/05_2026-10-20_to_11-03_collect-root/`](../archive/05_2026-10-20_to_11-03_collect-root/) — 174 later files from the root of the merged collection, including the October 23 four-panel X2D set and the November 3 Bambu Studio shortcut.
7. [Current tracked project](../README.md) — the main repository's reproducible scripts, prompts, and tracked grayscale master. The original engineering history is linked to [GitHub issues #1–#14](https://github.com/NeonButrfly/demiurge-mural/issues).

Source groups overlap in date range, so the numbered groups are ordered by their earliest source date. Files within each group are placed under the source file's last-write date. Those timestamps are useful chronology evidence, but they do not prove when an image was first created.

## Work lineage

| Period | Work represented |
| --- | --- |
| 2026-09-09–2026-10-04 | Early mural images, first full-plate/panel relief experiments, and layout/source candidates. |
| 2026-10-05–2026-10-13 | Height-map, semantic-depth, HueForge, STL, and architecture experiments. |
| 2026-10-12 | Four 400 mm panels, a continuous 800 mm image, calibrated relief meshes, circle restoration, and seam repair. Tracked in issues #1–#9. |
| 2026-10-14–2026-10-20 | Gothic Repair Suite handoff, targeted repair masks, grayscale/cybernetic composites, anatomy cleanup, and celestial restoration/layout correction. Tracked in issues #10–#11 and the [prompt records](prompts/). |
| 2026-10-20–2026-10-23 | Additional targeted figure/architecture edits, grayscale and height-map alternatives, and the four-panel 220 mm X2D set. The accompanying note specifies 440 × 440 mm total, 2.4 mm base, and 24.10 mm maximum height. It leaves slicing and physical seam fit unconfirmed. |
| 2026-11-03 | The latest timestamp in the merged collection belongs to a Bambu Studio shortcut, not a newer model revision. |

## Exclusions and validation limits

Regenerable virtual environments, runtime dependency directories, Python bytecode/cache files, Git metadata for the separately hosted source project, and its local `.env.local` were not copied into the main archive. The Gothic Repair Suite working tree was clean and its `main` commit matched its GitHub remote before archiving; its history remains at the linked source repository. The `.env.local` file was excluded to keep local configuration/secrets out of GitHub.

The 2026-10-23 X2D set has four STL panels and a panel 1 X2D 3MF. Bambu Studio slicing, printer placement, physical seam fit, and physical printing are not verified here. The archived X2D geometry and the main repository's October 19 grayscale master are different workflow outputs; the archive does not claim that the X2D files were regenerated from that master.

Initial consolidation: [issue #12](https://github.com/NeonButrfly/demiurge-mural/issues/12). The additional sources are integrated under [issue #14](https://github.com/NeonButrfly/demiurge-mural/issues/14); removal of their local copies remains blocked by the active filesystem policy. No milestone is assigned; this is archive/documentation work.
