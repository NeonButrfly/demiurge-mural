# V12 copper cybernetic filigree

Tracking: GitHub issue [#14](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/14). No milestone; this is a focused surface-treatment enhancement.

## Captured request

“readd cybernetic filigree in copper add more cybernetic flair use the above as an example do not use art as replacement”

## Interpretation

- The v11 repaired raster is the immutable composition and anatomy source.
- The supplied 2048 copper Demiurge artwork is a palette and motif reference only.
- Add fine aged-copper circuit traces, joint collars, mechanical ports, segmented conduits, cable connectors, and restrained inlays.
- Keep faces, anatomy, poses, figures, wings, architecture, halos, celestial circles, and grayscale relief modeling unchanged.
- Do not apply a broad orange wash or transplant any reference pixels.

## Implementation

The built-in reference-guided generative edit was blocked because the source composition contains exposed figures. V12 therefore derives a copper palette from the reference and draws a separate deterministic BGRA cybernetic overlay. The final is the unchanged v11 raster plus that overlay; all non-overlay pixels remain byte-identical.
