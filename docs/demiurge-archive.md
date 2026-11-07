# Demiurge archive and chronology

This index gathers the merged `demiurge-collect` project collection in this repository. The archive is ordered from the oldest work to the newest, using the collection's earlier nested `demiurge` folder first, then the later files from the collection root. Each set is grouped by the source file's last-write date. The original filenames and file bytes are preserved.

See [the SHA-256 inventory](../archive/manifest.csv) for each source file's date, size, original name, archived path, and hash. The archive currently contains 276 files totaling 2,469,742,764 bytes. Binary assets are stored with Git LFS.

## Chronological hierarchy

1. [`archive/01_earliest/`](../archive/01_earliest/) — earlier collection, spanning 2026-09-18 through 2026-10-20. This contains the first full-plate and panel relief files, source images, height-map and semantic-depth experiments, previews, and the 2026-10-19 macOS continuation bundle. The JSON beside that ZIP records its source commit, SHA-256, byte count, and ZIP-integrity check.
2. [`archive/02_latest/`](../archive/02_latest/) — later collection-root files, spanning 2026-10-20 through 2026-11-03. It preserves the follow-on artwork repair and grayscale candidates, source/reference crops, height maps, previews, and X2D panel deliverables.
3. [Current tracked project](../README.md) — the reproducible repository workflow and its documented current master. Prompt and engineering history is linked to [GitHub issues #1–#12](https://github.com/NeonButrfly/demiurge-mural/issues). Issue #12 tracks this archival consolidation.

## Work lineage

Dates below summarize the known task sequence and are cross-linked to the repository's prompt records and Git history. They describe the development lineage, not a claim that every exploratory image is a final result.

| Period | Work represented |
| --- | --- |
| 2026-09-18–2026-10-04 | Early single-panel and full-plate relief experiments, initial printable models, and layout/source candidates. |
| 2026-10-05–2026-10-09 | Full-resolution bas-relief experiments, height-map blending, grayscale tonal and architecture-depth variants, and detail restoration. |
| 2026-10-12 | Four 400 mm panels, a continuous 800 mm image, calibrated relief meshes, circle restoration, and seam repair. Tracked in issues #1–#9. |
| 2026-10-14–2026-10-20 | Mural repair handoff, neutral-grayscale and cybernetic composites, anatomy cleanup, and celestial restoration/layout correction. Tracked in issues #10–#11 and the [prompt records](prompts/). |
| 2026-10-20–2026-10-23 | Additional targeted figure and architecture edits, grayscale/height-map exploration, and the four-panel X2D export set. The archived handoff note says 440 × 440 mm total, four 220 × 220 mm panels, 2.4 mm base, and 24.10 mm maximum total height. It explicitly leaves Bambu Studio slicing and physical seam fit unconfirmed. |
| 2026-11-03 | Latest timestamp in the merged collection is a Bambu Studio shortcut; it is retained as part of the source collection and does not indicate a newer model revision. |

## Current endpoint and limits

The latest dated model deliverables in the merged collection are in `archive/02_latest/2026-10-23/`: four 220 mm panel STLs, a panel 1 X2D 3MF, previews, and the accompanying layout/clearance note. These are later than the repository's October 19 grayscale-master commits. The 3MF is present for panel 1 only; the other three archived panels are STL files. The 2026-11-03 shortcut is not treated as a design revision.

The current repository README identifies the latest tracked grayscale master as `outputs/grayscale_cybernetic_composite_v3/demiurge_grayscale_cybernetic_anatomy_corrected_celestials_2048.png`. The archived X2D geometry and the grayscale master represent different workflow outputs; do not infer that the X2D files were regenerated from that master without comparing their source metadata. No Bambu Studio slice, printer placement, physical seam-fit, or physical print validation is claimed here.

Archive task: [GitHub issue #12](https://github.com/NeonButrfly/demiurge-mural/issues/12). No milestone is assigned because this is historical documentation and archive work.
