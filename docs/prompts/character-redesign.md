# Prompt capture: three character groups for the Demiurge mural

Tracking: GitHub issue [#16](https://github.com/NeonButrfly/demiurge-mural/issues/16). Status: generated and composited; open for visual acceptance and refinement. No milestone; this is a focused artwork redesign.

## User request

The user marked two men yellow, the central reclining figure cyan, and the right-side demon magenta. They asked for the men to become something unique and better aligned with the mural, disliked the central figure, and wanted the demon to be more special. The user has repeatedly required local edits that preserve every unrelated part of the image.

## Interpretation and execution

- Yellow: replace generic men with a feathered bird-masked ritual inquisitor and a hooded astrolabe-bearing scribe.
- Cyan: replace the reclining figure with a chained celestial oracle in a similar diagonal pose, with carved armor, drapery, and a cracked halo.
- Magenta: replace the generic demon with an eclipse-crowned archdemon, ornate carapace, black circular chest hollow, and folding wings.

Each marked crop was separately generated with Qwen Image Edit Spicy. The three accepted outputs were composited into the clean 2048 x 2048 mural through local masks. The marked 2047 x 2047 desktop image served only to define the edit regions. The artifact is `outputs/mural_character_redesign/demiurge_redesigned_three_groups.png`.

## Validation

`outputs/mural_character_redesign/validation.json` records source/output hashes, generation IDs, and pixel checks. The final remains 2048 x 2048. Exactly 407,883 pixels changed; zero changed pixels are outside the three allowed edit masks. The examined Kharn Sagara region is byte-identical to the source. Full frame, 512-pixel preview, and edited-region crops were reviewed. This validates local raster integration, not physical relief or print quality.

## Bridge review

The user's follow-up asks for a whole-image critique as the bridge centerpiece. The review is in `docs/reviews/demiurge-bridge-mural.md`. The most concrete separate defect is the earlier three-woman insert boundary, tracked in [#17](https://github.com/NeonButrfly/demiurge-mural/issues/17). Issue #16 remains open because the revised character designs have not been accepted by the user and still need style/hierarchy evaluation.

## Later art direction and rejected variants

The user then asked for a disturbing, sexual, sensual, violent bridge mural, with all parts flowing together in the same theme. Three further Qwen Spicy candidates were tested locally. The translucent-mask trio and demon runs made almost no meaningful changes. The solid-mask nonhuman demon run left pink markup, added blue lightning, and broke the monochrome relief style. All three were rejected and **none was composited** into the final mural. Their generation IDs and the final output hash are in `outputs/mural_character_redesign/final_validation.json`.

The accepted follow-up is a narrow, deterministic blend at the three-woman insert's upper and lower borders. It uses the earlier 2048-pixel mural background and retains the prior accepted figures. The current artifact is `outputs/mural_character_redesign/demiurge_bridge_flow_refined.png`. The user's latest sensual/violent art direction remains an open design requirement in #16; the failed Qwen variants do not satisfy it.
