# Prompt capture: fix3 colored-patch repair

Tracking: GitHub issue [#15](https://github.com/NeonButrfly/demiurge-mural/issues/15). Status: completed and closed. No milestone; this is a focused artwork correction.

## User request

The user supplied `fix3.png` with the message “fix3”. After clarification, the user confirmed that the bright patches should be repaired into grayscale artwork and that `fix3.png` itself is the edit base. The user emphasized that only the marked portions should be regenerated.

## Interpreted requirement

Repair the cyan, magenta, yellow, and orange/green markings in the lower mural. Match the surrounding black-and-silver engraved relief and preserve the supplied composition and all unmarked pixels. Keep the original file unchanged.

## Edit workflow

The whole-image edit was rejected by output moderation. The repair then used five separate close crops: cyan, magenta, yellow, right vertical olive mark, and lower-right orange/olive marks. Each crop was generated independently. The composite applies those outputs only through local color masks and three tight masks for dark blocks belonging to the same annotations. Residual colored edge pixels inside the same marked zones were converted using source luminance. The rest of `fix3.png` was copied unchanged.

## Validation

- Confirmed source and output are both 2047 × 2047 PNGs.
- Full frame and close views of the edited areas were visually reviewed.
- The repair mask covers 101,794 pixels; 101,640 pixels differ from the source.
- No changed pixels fall outside the repair mask.
- All changed pixels are neutral grayscale, and no residual pixels above the recorded chroma threshold remain in the localized cleanup areas.
- The input source remains unchanged. Source and output SHA-256 hashes are in `outputs/fix3_repair/repair_manifest.json`.

## Remaining limits

Generated detail inside the selected areas may vary from the original anatomy and engraving. Relief conversion, slicer use, physical fit, and print results were not tested.
