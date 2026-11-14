# Bridge mural integration refinement

Tracking: [#17](https://github.com/NeonButrfly/demiurge-mural/issues/17) for the three-woman insert and [#19](https://github.com/NeonButrfly/demiurge-mural/issues/19) for Kharn Sagara and the authority-to-captivity read. Both belong to the `Demiurge Bridge Mural Harmony` milestone.

## User requirement

The user asked to fix the smoother trio material and dark drapery join, then make Kharn Sagara legible at distance, then sharpen the ideological relationship between ruling power and bound people through existing figures and contrast. They explicitly did not want another symbol or person. Their established constraint is local edits only.

## Current result

`outputs/bridge_refinement/demiurge_bridge_refined.png` is the 2048 x 2048 current raster. `scripts/refine_bridge_mural.py` reproduces it from the preceding accepted mural. The trio receives local stone grain and reduced smooth sheen, and the upper drapery transition is lifted slightly. Kharn's immediate architectural background is quieted, his existing robe and pose are retained, and only his head/neck area receives a Qwen Image Edit Spicy refinement (generation `3M51wq4seUCaHvj3cWj3GHZxjRA`). The upper skeletal ring, bound oracle, and existing chain receive locally separated values. No person, symbol, or color was added.

Two broader Qwen Kharn candidates (`3M50pqxrXgpJxFtd7c7qzQ1kMgR`, `3M51FUsSzPyju7fm84gMDhs7gJ2`) were rejected because they made him a smooth, muscular comic-book figure and changed the original pose. A broad dark shaft test was also rejected because it added an artificial spotlight effect.

## Validation and limits

`outputs/bridge_refinement/refinement_validation.json` records the source and output hashes, pixel-locality check, and zero strong-color pixels. Full-size trio, oracle, and Kharn crops and the 512-pixel before/after view were inspected. The value changes improve the reading, but the full mural remains deliberately dense: Kharn and the chains are still small at 512 pixels. The current 16-bit heightmap, virtual raking-light render, and 100 x 100 mm trio and Kharn STL samples are in `outputs/bridge_refinement/`. Both meshes are watertight with 66,560 faces and 100 x 100 x 15 mm bounds. No physical print or installed bridge-light check has been performed.
