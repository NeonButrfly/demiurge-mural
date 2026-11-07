# Image-repair prompt capture

## Local Gothic repair suite — GitHub #1

- Source: user request continued from “Analyze Gothic Composition.”
- Tracking: [Issue #1](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/1)
- Milestone: `Local Image Repair Suite v1`
- Interpreted requirement: provide a usable local Windows application for targeted, mask-first repairs to Pass 7 without regenerating or modifying the rest of the artwork.
- Affected behavior: canvas navigation, masks, defect checklist, candidate workflow, local/remote inpainting, donor repairs, compositing, history, project persistence, QA and export.
- Required defect regions: central feet & shins; reclining hip/legs; hooded cybernetic hand; floating arms; spear grip.
- Acceptance constraint: pixels outside approved masks remain byte-identical at the working resolution, with automated assertion and visible violation output.
- Asset state: the original, central-legs mask, and mask preview supplied by the user are preserved under `assets/`.

## Pass 7 central feet and shins repair — GitHub #2

- Tracking: [Issue #2](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/2)
- Requirement: repair only the supplied central-legs mask, create continuous legs/ankles/feet with five distinct toes per visible foot, and preserve all unselected pixels exactly.
- Method: generate a focused 260×260 anatomical candidate from the original crop, then apply it with the original grayscale mask through `scripts/composite_generated_repair.py`.
- Invariant: every pixel where the supplied mask is zero must remain byte-identical to `Gothic_Relief_Pass_7_Original.png`.
- Scope boundary: other malformed anatomy in the full artwork remains unchanged because it is outside the supplied mask.

## Additional local anatomy repairs — GitHub #3 and #4

- Tracking: [Issue #3](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/3) and [Issue #4](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/4).
- Hooded cybernetic hand: a dedicated 5,165-pixel mask isolates the fused wrist/hand cluster without touching the hooded face or the neighboring figure's face.
- Spear grip: a dedicated 2,542-pixel mask isolates the gripping wrist, hand, fingers, and immediate shaft intersection without touching the spear-holder's face or neck.
- Cumulative output: `Pass7_Anatomy_Repairs_v2.png` contains the previously approved central-feet repair plus the two new approved local repairs.
- Validation: the union of all three approved masks contains 20,830 pixels; every pixel outside that union remains byte-identical to the original Pass 7 source.
- Follow-on scope: [Issue #5](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/5) covered the reclining-body/hip fusion and is completed by the full cleanup pass below.
- Follow-on audit: [Issue #6](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/6) covered floating or ambiguously owned arms and is completed by the full-resolution review below.

## Full anatomy cleanup continuation — GitHub #5 and #6

- User requirement: remove disconnected or duplicated limbs, fused bodies, malformed hands, impossible joints, and anatomy that dissolves into surrounding figures or ornament; every visible limb must have an identifiable owner.
- Tracking: [Issue #5](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/5) for the reclining hip/legs and [Issue #6](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/6) for the arm-ownership audit.
- Reclining repair: `Pass7_Reclining_Hip_Legs_Mask.png` confines a same-artwork donor transform to the malformed lower-body area. Approved legs, feet, and drapery from Pass 7 are luminance-matched and feather-composited without touching neighboring faces outside the mask.
- Arm audit: the lower-center shoulder-to-hand chain was inspected at 4× pixel zoom. It has a continuous owner, so no edit was approved; replacing valid anatomy would violate the mask-first scope.
- Cumulative output: `Pass7_Anatomy_Cleanup_v3.png` contains four approved repairs. The 41,389-pixel union of their masks is the complete allowed-change area.
- Validation: every pixel outside that union remains byte-identical to the untouched original. The difference image and out-of-mask violation image are exported beside the result.
- Backend boundary: two focused image-generation attempts were rejected by the service safety system because the classical bas-relief crop contains nudity. The accepted v3 repair therefore uses the suite's implemented local donor-transform path; the failed generations changed no files.

## Corrected center audit — reopened GitHub #6 and GitHub #7

- User correction: the v3 review still left many intermixed bulbous forms and a distended central arm/hand with no owner.
- Tracking: [Issue #6](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/6) was reopened because its prior no-edit conclusion was wrong, then closed after the corrected repair passed QA. [Issue #7](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/7) was created and closed for the adjoining bulbous-form cluster.
- Arm repair: `Pass7_Ownerless_Center_Arm_Mask.png` follows the disconnected raised hand and long arm without including the neighboring woman's torso, skull figure, helmeted face, or valid foreground arm.
- Bulb repair: `Pass7_Central_Bulbous_Forms_Mask.png` isolates six rounded growths adjoining the arm while preserving recognizable skulls and owned anatomy.
- Method: the built-in image-editing backend generated non-anatomical feather/drapery relief from safety-obscured references. Only the two reviewed masks are composited into Pass 7; the obscured safety-reference areas are never used.
- Final output: `Pass7_Anatomy_Cleanup_v4.png`. The cumulative six-mask union contains 56,766 pixels, and every pixel outside that union remains byte-identical to the original.
- Prompt intent: replace only opaque-red defect areas with sharp black-and-silver feather layers, cloth folds, or recessed negative space; introduce no body, limb, face, skull, sphere, text, color, blur, border, or watermark.

## User-highlighted robe extrusions — reopened GitHub #7

- User input: `references/Pass7_Highlighted_Extrusions_User.png`, containing two red marks over remaining bulbous robe protrusions.
- Tracking: [Issue #7](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/7) was reopened for the two annotated residual defects and closed after the v5 masks, visual review, and invariant tests passed.
- Mask derivation: the preparation script detects pixels whose red channel exceeds both other channels by at least 55, closes marker gaps, builds one convex component mask per annotation, and applies constrained internal feathering.
- Repairs: `Pass7_RobeExtrusion_Mask.png` contains 3,442 selected pixels; `Pass7_UpperExtrusion_Mask.png` contains 1,925 selected pixels.
- Method: two separate built-in precise-object edits replaced the marked protrusions with directional robe folds. The generated crops are luminance-matched and strictly composited only inside the masks.
- Final output: `Pass7_Anatomy_Cleanup_v5.png`; cumulative eight-mask union 62,133 pixels; zero changed pixels outside the union.
- Prompt intent: replace the red bulbous extrusion with continuous engraved cloth following surrounding fold direction; preserve every non-red figure, face, object, and composition detail; add no lump, body part, object, color, blur, text, border, or watermark.

## User-highlighted central arm removal — reopened GitHub #6

- User input: `references/Pass7_Highlighted_Unwanted_Arm_User.png`, with a red mark over the unwanted forearm and hand crossing the central robes.
- Tracking: [Issue #6](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/6) was reopened for this newly annotated residual arm and closed after the v6 visual review, automated tests, and byte-identity QA passed.
- Mask derivation: `prepare_highlighted_arm_removal.py` extracts the red annotation, closes marker gaps, convex-fills its single component, dilates it by five pixels for complete coverage, and applies constrained internal feathering. The resulting approved mask contains 4,850 selected pixels.
- Method: the built-in precise image-edit mode replaces the selected arm/hand footprint with continuous layered robe folds and recessed shadow. The generated crop is converted to grayscale, luminance-matched to the v5 context, and strictly composited inside the approved mask only.
- Final output: `Pass7_Anatomy_Cleanup_v6.png`; the QA report records the cumulative nine-mask union and zero changed pixels outside it.
- Prompt intent: remove only the red-marked arm and hand; replace its footprint with sharp black-and-silver cloth relief that follows the surrounding folds; preserve the valid clasped hands above, faces, torsos, pose, lighting, texture, and every unselected pixel; add no new anatomy, color, blur, seam, text, border, or watermark.

## Reference-driven motif restoration — GitHub #8

- User requirement: restore halos, cybernetic body modifications, exposed classical adult anatomy, and body-following wires to the corrected v6 composition, using the supplied 2048×2048 grayscale four-panel Demiurge source as the reference.
- Tracking: [Issue #8](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/8) was closed after the 2048 master, three detail crops, neutral-grayscale check, automated tests, and packaged QA passed. No milestone is assigned because this is one artwork revision rather than a new repair-suite system.
- Preserved reference: `assets/references/Demiurge_Four_Panel_Restoration_Reference_2048.png`, SHA-256 `67de2583465d0de522d3084a3abc8a4f18bd708132164b4560a68ea146c3804a`.
- Intended invariants: v6 remains the edit target; retain its figure count, faces, pose layout, corrected anatomy, architecture, wings, skulls, celestial circles, border, lighting, and monochrome bas-relief treatment.
- Built-in boundary: two built-in image-edit attempts were rejected by the service's output safety filter with category `sexual`; no candidate image was returned or saved from those attempts.
- Approved fallback: after the user explicitly approved CLI/API mode, a project API key was securely provisioned to the ignored `.env.local` file. The bundled `image_gen.py` edit path used `gpt-image-2`, high quality, two ordered inputs, and a 2048×2048 output.
- Final output: `outputs/Pass7_Anatomy_Cybernetic_Restoration_v7.png`, with an additional 1254×1254 compatibility copy, difference view, three detail crops, and JSON QA report.
- Scope distinction: v7 is an intentional whole-image reference-guided restoration. The earlier strict mask-only byte-identity invariant is therefore not applicable; the untouched v6 remains the preserved local-repair baseline.
- Prompt intent: keep v6 as the composition and identity target; use the 2048 source only to restore circular/radial halos, nonsexual classical adult sculptural anatomy, engraved cybernetic plates/ports/joint seams, and ribbed cables with believable body attachments; add no new figures, malformed anatomy, floating wires, color, text, or watermark.

## Original Pass 7 halo restoration — GitHub #9

- User requirement: restore the original halo designs after the v7 global cybernetic restoration.
- Tracking: [Issue #9](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/9). No milestone is assigned because this is a single localized artwork correction.
- Edit target: `outputs/Pass7_Anatomy_Cybernetic_Restoration_v7.png`; authoritative halo reference: the untouched `assets/Gothic_Relief_Pass_7_Original.png`.
- Scope: only the two concentric engraved halo rings behind the upper central women. The annular mask protects the foreground faces and hair and excludes the left and right celestial orbs.
- Method: a high-quality 2048×2048 `gpt-image-2` edit uses v7 as Image 1 and the untouched Pass 7 source as Image 2. The generated candidate is converted to neutral grayscale and composited with an eight-pixel internal feather strictly inside `Pass7_Original_Halos_Selection.png`.
- Invariant: every v7 pixel outside the approved halo selection remains byte-identical. QA exports include a difference view, an out-of-mask violation image, a detail crop, and a JSON report.
- Prompt intent: restore the original Pass 7 halo geometry, concentric rings, radial engraving, metallic highlights, shadows, and relief depth; retain all v7 faces, bodies, cybernetics, wires, wings, architecture, skulls, lighting, and composition; add no color, text, or watermark.

### Corrected source and destination

- User correction: the previous v8 interpretation was rejected. The authoritative halo design source is `Demiurge_Four_Panel_Restoration_Reference_2048.png`, and the required destination is `Pass7_Anatomy_Cleanup_v6.png`, not v7.
- Corrected scope: first pass changes only the two visible halos. The upper woman receives the source's simple mechanical ring halo; the lower/front woman receives the source's radial sunburst crown halo. Anatomy and every non-halo destination pixel are protected.
- Generation boundary: the reference-guided API attempt was rejected by the output safety filter. No API-generated pixels are used in the accepted result.
- Accepted method: deterministic affine donor transfer from the supplied 2048 source, tonal-range matching, and four-pixel internal feathering through `Pass7_v6_Source_Halos_Selection.png`.
- Corrected output: `outputs/Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png`. Automated QA asserts zero changed pixels outside the halo selection.

## PDF-annotated anatomy repairs — GitHub #10

- User input: `10152026.pdf`, with yellow marks identifying anatomy to repair and red marks requiring complete removal and replacement, especially the lower reclining figure.
- Tracking: [Issue #10](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/10). No milestone is assigned because this is a single artwork revision.
- Destination: `outputs/Pass7_Anatomy_Cleanup_v6_Halos_Pass1.png`; the halo pass and every unmarked pixel remain protected.
- Registration: ORB feature matching aligns the scanned/rotated PDF page to the 1254×1254 destination with 3,586 homography inliers. HSV annotation extraction yields 95,060 yellow pixels and 57,128 red pixels.
- Red replacements: a coherent horned relief head, a distinct five-finger hand gripping the spear shaft, and a continuous reclining armored adult figure with connected hips, knees, calves, ankles, feet, shoulders, elbows, wrists, and hands.
- Yellow repair: marked malformed anatomy and bulbous forms are harmonized into surrounding monochrome drapery, feather, armor, cable, and skull relief with Poisson blending.
- Safety boundary: a full-source edit was blocked by the output safety filter. The accepted result uses focused, non-explicit donor plates; no blocked candidate pixels were returned or used.
- Final output: `outputs/Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png`; the 151,872-pixel registered mask union is the complete allowed-change area, with zero changed pixels outside it.

## Cybernetic reintegration without anatomy changes — GitHub #11

- User requirement: replace the lower armored reclining donor with a grayscale-harmonized human figure carrying cybernetic filigree; make the upper-right demon hand unmistakably a connected claw; restore cybernetics on the hooded figure's arm and add restrained electronic filigree among existing bodies without changing anatomy. Perform a completion analysis afterward.
- Tracking: [Issue #11](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/11). No milestone is assigned because this is a localized artwork revision rather than a repair-suite subsystem.
- Destination: `outputs/Pass7_Anatomy_Cleanup_v7_PDF_Repairs.png`; reference: `assets/references/Demiurge_Four_Panel_Restoration_Reference_2048.png`.
- Generation boundary: the built-in full-image edit was blocked by the output safety filter because the reference contains classical nudity. No blocked candidate was returned or used. The previously approved CLI/API fallback generated four non-explicit focused donor plates.
- Anatomy policy: only the existing reclining replacement silhouette may receive a new human figure. The hooded arm and five body regions receive surface-only engraved details, not reshaping. The demon claw occupies the prior ambiguous upper-right object mask.
- Final output: `outputs/Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration.png`; 86,896 pixels are inside the approved mask union, 85,286 pixels changed, and zero pixels changed outside the union.
- Completion analysis: `outputs/Pass7_Anatomy_Cleanup_v8_Cybernetic_Reintegration_Analysis.md` records the limb-continuity, ownership, cybernetic attachment, grayscale, and preservation review.

