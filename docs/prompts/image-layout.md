# Prompt capture: four-panel Demiurge mural layout

Linked issue: [#1](https://github.com/NeonButrfly/demiurge-mural/issues/1)

## Original request

“Expand this out maintaining detail so that each corner panel fits a ender 5 max bed 400x400 add a 5mm thin low z border around the outside edges do not exceed the 400x400 do not remove any details. Regnerate grayscale image. This should be a git enabled project with tracking following comit rules make sure the provided image is added to the project.”

## Interpreted requirement

Keep the supplied grayscale artwork as the source of truth, split it into four equal corner regions, fit each region inside a 390 × 390 mm artwork area, and surround it with a 5 mm low-Z border so the complete panel remains 400 × 400 mm.

## Affected systems

- Artwork source and grayscale raster assets
- Four-panel crop/layout generation
- Relief or heightmap preparation
- GitHub issue and project documentation

## Expected behavior

All four panel files are grayscale, preserve their corresponding source quadrant content, include a uniform 5 mm low-Z outside border, and remain within the 400 × 400 mm bed envelope.
