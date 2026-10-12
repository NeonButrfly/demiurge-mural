# Prompt capture: quarter-panel seam repair

Linked issue: [#9](https://github.com/NeonButrfly/demiurge-mural/issues/9)

Milestone: [Demiurge 800mm Bas-Relief](https://github.com/NeonButrfly/demiurge-mural/milestone/1)

## Original request

“repair the seems between each 1/4 panel there are images that are mismatched and drift maintain as much of original image as possible”

## Interpreted requirement

Repair the visible hard transitions at the exact 1024-pixel horizontal and vertical splits of the supplied 2048 × 2048 source. Preserve the original composition and detail by limiting all changes to the smallest practical center bands, rather than regenerating or broadly retouching the mural.

## Affected systems

- Color source artwork
- Four-panel crop and assembly workflow
- Seam validation previews and metrics

## Implementation

Issue #9 uses a cubic, gradient-continuous bridge across four pixels on each side of each center join. The tangent-shift measurements are retained as diagnostics but are not applied as broad panel warps because those warps visibly soften unrelated detail.

The built-in generative image editor was attempted twice, but its safety filter rejected the source artwork. No generated image was returned or used. The committed result is the deterministic narrow-band repair.

## Validation and limits

- Output remains 2048 × 2048 RGB PNG.
- 32,623 pixels changed (0.778% of the image).
- No pixel outside the declared seam bands changed.
- Mean vertical seam step decreased from 46.91 to 9.05 intensity levels.
- Mean horizontal seam step decreased from 43.07 to 8.64 intensity levels.
- Full master, both center-strip previews, changed-pixel mask, and four quadrant exports were inspected.
- This verifies the raster join repair only. Relief conversion, slicer placement, physical panel alignment, and printed seam appearance remain untested.
