# Prompt capture: celestial restoration and anatomy pass

Linked issue: [#11](https://github.com/NeonButrfly/demiurge-mural/issues/11)

Regression source: [#10](https://github.com/NeonButrfly/demiurge-mural/issues/10)

Milestone: [Demiurge 800mm Bas-Relief](https://github.com/NeonButrfly/demiurge-mural/milestone/1)

## Original request

“lost starfield and eclipse also do a anatomy pass”

Acceptance correction: “the starfield and eclipse should look like in this image”

## Interpreted requirement

Keep the issue #10 mural's neutral grayscale character, dense bodies, cybernetics, architecture, wings, and fine relief detail. Repair ambiguous body and cybernetic-limb transitions without redrawing the whole mural or changing faces. The supplied 1131 × 1131 grayscale image is authoritative for the celestial appearance and orientation: a cloudy dark eclipse with a bright soft rim at upper left, and a crisp star field inside a metallic circular rim at upper right.

## Affected systems

- Artwork and image-generation pipeline
- Celestial layout and composition
- Anatomy and cybernetic attachment continuity
- Relief-source preparation

## Execution

- Preserved the issue #10 2048 × 2048 grayscale master as the full-frame base.
- The original v2 execution placed the star field at upper left and the eclipse at upper right. The user rejected that orientation.
- Ran the cached `stabilityai/sd-turbo` model locally on CPU for three 512 × 512 anatomy crops.
- Blended each model proposal conservatively through a feathered polygon mask.
- Applied separate face-protection exclusions after mask feathering so heads retain a zero-edit core.
- Preserved every pixel outside the union of the eclipse and anatomy masks.
- In the accepted v3 correction, preserved the entire v2 anatomy master and transplanted only the two celestial circles from `celestial_layout_reference_1131.png`.
- Mapped the reference eclipse to the upper-left circle and the reference star field to the upper-right circle through separate feathered masks.

## Local anatomy prompt

“neutral grayscale gothic bas-relief, coherent sculptural anatomy, each arm connected from shoulder through elbow and wrist to one hand, biomechanical prosthetics attached at natural joints, no floating hands, no duplicated limbs, preserve composition, crisp cybernetic detail”

## Expected behavior

- The cloudy rimmed eclipse is at upper left and the crisp circular star field is at upper right, matching the supplied reference.
- The anatomy pass is local and improves limb ownership and attached cybernetic joints without replacing faces or the surrounding mural.
- The output remains a 2048 × 2048 neutral grayscale relief source.

## Validation boundaries

- Full-frame and detail crops are visually inspected.
- The manifest verifies identical RGB channels, source hashes, repair boxes, seeds, and zero changed pixels outside documented masks.
- The raw model crops are diagnostics; the conservatively blended crops are the accepted artwork.
- Relief conversion, slicer behavior, and physical printing remain unverified.
