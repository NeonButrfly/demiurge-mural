# Reviewed reintegration corrections

Tracking: GitHub issue [#12](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/12). No milestone; this is a focused repair of a rejected output.

## User review

- Yellow: the demon claw is not integrated with its arm and the adjacent wing forms are mixed.
- Red: remove the marked ownerless biological bulbs.
- Blue: replace the inconsistent reclining graft and match the composition's silver-black grayscale.
- Green: remove the inconsistent unattached heads.
- Purple: make the hooded cybernetic arm and hand follow the supplied original reference.

## Interpreted requirement

Use `outputs/Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png` as the clean destination rather than repairing on top of the rejected v8 grafts. Treat the user's annotated v8 image only as a selection map. Correct each selected region with sufficient surrounding context, preserve the original composition, and assert that every pixel outside the approved mask union remains byte-identical to v7.

## Validation

- Full-resolution and enlarged region inspection.
- Neutral grayscale channel equality.
- Exact 1254 x 1254 working dimensions.
- Zero changed pixels outside the approved mask union.
- Difference, mask-preview, out-of-mask, and JSON QA artifacts.
