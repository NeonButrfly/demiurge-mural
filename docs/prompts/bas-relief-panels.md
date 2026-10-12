# Prompt capture: four-panel 800 mm bas-relief

Linked issue: [#5](https://github.com/NeonButrfly/demiurge-mural/issues/5)

## Original request

“create a 3d bas relief include all elements raise where required this should be a total of 800x800 in 4 printable panels”

## Interpreted requirement

Convert the supplied continuous grayscale heightmap into four separate 400 × 400 mm printable bas-relief panels. Together they must form one continuous 800 × 800 mm mural.

## Production assumptions

- 2.5 mm solid base
- Up to 7.5 mm raised relief above the base
- 10 mm maximum total panel thickness
- 5 mm low-Z border on the outside perimeter only
- Shared source samples at internal seams so no artificial seam border is added

STL mesh validation does not establish slicer acceptance or physical print fit.
