# Prompt capture: architecture and circular-element depth adjustment

Linked issue: [#3](https://github.com/NeonButrfly/demiurge-mural/issues/3)

## Original request

“adjust the grayscale image so that the archictecture, left and right elements including the circles have more depth”

## Interpreted requirement

Increase grayscale relief separation in the left and right architectural/background regions and circular elements while preserving the continuous artwork, central figures, grayscale format, and existing outer border.

## Processing constraint

Use a deterministic masked contrast and local-edge enhancement. The original image remains available as the unmodified baseline; the enhanced version is saved as a separate artifact.

## Follow-up restoration

Linked issue: [#7](https://github.com/NeonButrfly/demiurge-mural/issues/7)

User request: “these are correct panels except for the circle star and the circle eclipse and sourounding area” followed by “restore regions”.

The restoration variant composites the original grayscale baseline back into feathered upper-left and upper-right masks covering the star circle, eclipse circle, and their immediate surrounding architecture. The remaining enhanced artwork and the 5 mm low-Z perimeter are preserved.

## 250 mm geometry-preserving correction

Linked issue: [#8](https://github.com/NeonButrfly/demiurge-mural/issues/8)

The supplied Desktop panels remain the geometry source. The corrected outputs preserve each input panel’s 250 × 250 mm XY bounds, triangle order, topology, and individual maximum Z; only local Z values in the masked circle regions are adjusted. Lower panels are copied byte-for-byte.
