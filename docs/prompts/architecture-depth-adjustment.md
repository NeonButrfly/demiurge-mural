# Prompt capture: architecture and circular-element depth adjustment

Linked issue: [#3](https://github.com/NeonButrfly/demiurge-mural/issues/3)

## Original request

“adjust the grayscale image so that the archictecture, left and right elements including the circles have more depth”

## Interpreted requirement

Increase grayscale relief separation in the left and right architectural/background regions and circular elements while preserving the continuous artwork, central figures, grayscale format, and existing outer border.

## Processing constraint

Use a deterministic masked contrast and local-edge enhancement. The original image remains available as the unmodified baseline; the enhanced version is saved as a separate artifact.
