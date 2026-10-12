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
