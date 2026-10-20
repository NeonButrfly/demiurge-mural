# Prompt capture: celestial restoration and anatomy pass

Linked issue: [#11](https://github.com/NeonButrfly/demiurge-mural/issues/11)

Regression source: [#10](https://github.com/NeonButrfly/demiurge-mural/issues/10)

Milestone: [Demiurge 800mm Bas-Relief](https://github.com/NeonButrfly/demiurge-mural/milestone/1)

## Original request

“lost starfield and eclipse also do a anatomy pass”

## Interpreted requirement

Keep the issue #10 mural's neutral grayscale character, dense bodies, cybernetics, architecture, wings, and fine relief detail. Restore two distinct celestial features from the authoritative color composition: the bright star field at upper left and the dark eclipse with a luminous corona at upper right. Repair ambiguous body and cybernetic-limb transitions without redrawing the whole mural or changing faces.

## Affected systems

- Artwork and image-generation pipeline
- Celestial layout and composition
- Anatomy and cybernetic attachment continuity
- Relief-source preparation

## Execution

- Preserved the issue #10 2048 × 2048 grayscale master as the full-frame base.
- Kept the upper-left star field unchanged.
- Restored the upper-right eclipse from the color reference's luminance after matching the grayscale reference's tone distribution.
- Ran the cached `stabilityai/sd-turbo` model locally on CPU for three 512 × 512 anatomy crops.
- Blended each model proposal conservatively through a feathered polygon mask.
- Applied separate face-protection exclusions after mask feathering so heads retain a zero-edit core.
- Preserved every pixel outside the union of the eclipse and anatomy masks.

## Local anatomy prompt

“neutral grayscale gothic bas-relief, coherent sculptural anatomy, each arm connected from shoulder through elbow and wrist to one hand, biomechanical prosthetics attached at natural joints, no floating hands, no duplicated limbs, preserve composition, crisp cybernetic detail”

## Expected behavior

- The two celestial objects are visibly different and remain in their original upper-left and upper-right positions.
- The anatomy pass is local and improves limb ownership and attached cybernetic joints without replacing faces or the surrounding mural.
- The output remains a 2048 × 2048 neutral grayscale relief source.

## Validation boundaries

- Full-frame and detail crops are visually inspected.
- The manifest verifies identical RGB channels, source hashes, repair boxes, seeds, and zero changed pixels outside documented masks.
- The raw model crops are diagnostics; the conservatively blended crops are the accepted artwork.
- Relief conversion, slicer behavior, and physical printing remain unverified.
