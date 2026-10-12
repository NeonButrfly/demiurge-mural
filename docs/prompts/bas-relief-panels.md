# Prompt capture: four-panel 800 mm bas-relief

Linked issue: [#5](https://github.com/NeonButrfly/demiurge-mural/issues/5)

## Original request

“create a 3d bas relief include all elements raise where required this should be a total of 800x800 in 4 printable panels”

## Interpreted requirement

Convert the supplied continuous grayscale heightmap into four separate 400 × 400 mm printable bas-relief panels. Together they must form one continuous 800 × 800 mm mural.

## Production assumptions

- 2.5 mm solid base
- Up to 22.6175 mm raised relief above the base
- 25.1175 mm maximum total panel thickness, calibrated from the supplied example STL
- Gamma 0.30 grayscale lift so dark but meaningful details remain raised
- 5 mm low-Z border on the outside perimeter only
- Shared source samples at internal seams so no artificial seam border is added

STL mesh validation does not establish slicer acceptance or physical print fit.
