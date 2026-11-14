# Demiurge mural review for bridge display

Reviewed artifacts: `outputs/mural_character_redesign/demiurge_redesigned_three_groups.png` and the later seam-refined `outputs/mural_character_redesign/demiurge_bridge_flow_refined.png` (both 2048 x 2048 raster). Review requested by the user after the three local redesigns. This is a visual assessment, not a physical print, mesh, or installed bridge inspection. Tracking: [#16](https://github.com/NeonButrfly/demiurge-mural/issues/16); pre-existing three-woman insert boundary [#17](https://github.com/NeonButrfly/demiurge-mural/issues/17).

## What works

- The three revised regions are integrated into the same canvas. Gothic architecture, circular celestial motifs, wings, and central vertical structure still convey a large cosmological setting.
- The bird-masked attendant, bound oracle, and eclipse-crowned demon each have clearer identities than the replaced figures.
- At a 512-pixel distance preview, the wing span, upper central spoked ring, right celestial discs, and lower angel remain legible.

## Ranked findings

1. **High: three-woman insert boundary.** The lower-right trio had a visible straight-edged transition at its upper-left and lower borders. A narrow, irregularly feathered blend improved the upper and lower edges without changing the figures or Kharn Sagara. Some difference in carving style remains, so #17 stays open.
2. **High: focal hierarchy for bridge viewing.** At 512 pixels the mural reads first as a dense field of arches and wings. The upper skeletal face, oracle, demon, and celestial medallions compete rather than form one obvious visual axis. Decide which symbol/person is the authority of the bridge scene. Give that one larger value separation and calm a little adjacent background detail; avoid adding more figures.
3. **Medium: style mismatch in newly generated figures.** The oracle has a smooth bright face and crisp engraved cuirass; the demon is smooth and nearly symmetrical; the dark scribe is close to a black silhouette. Surrounding figures are noisier and more organically carved. Match edge texture, midtone range, and relief depth locally before producing a heightmap.
4. **Medium: demon still reads as a familiar winged humanoid at distance.** Crown rays and chest void are specific at full size but collapse into small spikes and a dot at bridge distance. Make one silhouette feature decisive, such as a larger eclipse crown or asymmetric wing, rather than adding fine markings.
5. **Medium: Kharn Sagara's visual identity is weak.** The lower-right seated figure remains relatively small and is visually absorbed by drapery, skulls, and architecture. If Kharn Sagara is a required story anchor, strengthen the figure's silhouette or distinct emblem locally. Do not replace the nearby trio.
6. **Medium: 3D relief readability is unverified.** At an 800 mm final width, one source pixel spans about 0.39 mm. Fine engraving, fingers, facial features, and the demon's crown spikes can vanish or become fragile in conversion. Test a depth preview and small physical crop under intended bridge lighting before committing to a full print.
7. **Low: small background heads and hands are ambiguous.** Several tiny crowd figures are stylized or partially fused at native resolution. They are subordinate at distance; prioritize only ones that become conspicuous in the intended print/lighting.

## Recommended sequence

Finish the remaining style integration in #17. Then choose the intended main bridge focal point and adjust contrast, not layout. Next harmonize the three new figures' material treatment and enlarge one defining feature of the demon. Finally produce a current-version depth map and print a representative crop. Preserve the surrounding mural pixels in each change.

The later Qwen Spicy candidates were rejected because two repeated the existing figures and one produced obvious pink and blue artifacts. The accepted raster at that stage kept the earlier figures and included only the narrow seam blend. Further art changes should use a materially different reference or workflow, with candidate inspection before compositing.

An Age of the Mericanai correction then replaced the anachronistic bird-masked attendant with a kneeling adult nude woman. The current file is `outputs/mural_character_redesign/demiurge_bridge_mericanai_woman.png`. This removes the bird identity while preserving the scribe and oracle. Its small hand contact with the scribe remains the main anatomy detail to inspect if the scene is enlarged for relief production.

The added void-chested demon was later rejected as out of place. The current file is `outputs/mural_character_redesign/demiurge_bridge_mericanai_original_demon.png`, with the earlier integrated demon and masonry restored. This removes the smooth foreground figure and its circular chest void while leaving the Mericanai woman and Kharn Sagara unchanged. The broader bridge focal hierarchy and relief-depth questions remain unresolved.

## Current bridge harmony pass

Tracked in [#18](https://github.com/NeonButrfly/demiurge-mural/issues/18) under the `Demiurge Bridge Mural Harmony` milestone. The current artwork is `outputs/bridge_harmony/demiurge_bridge_harmonized.png`. The upper skeletal face and spoked ring are the visual authority. Restrained local value changes give that axis more separation, temper the oracle and trio highlights, reveal the scribe's dark robes, and distinguish Kharn Sagara's existing face and upper robe. The original integrated demon remains; the earlier recommendation to enlarge the rejected void demon is superseded.

The trio's most conspicuous left join now contains a narrow carved Gothic column generated in Qwen Image Edit Spicy (generation `3M4jdEm2lHDinvVst5wkM1twZyV`) and applied only through a feathered strip. The three women, nearby Kharn Sagara, and the rest of the mural were not regenerated. The top drapery and some material differences in the trio insert are still visible under close inspection, so #17 remains open for physical display review. The 512-pixel read remains dense, but the central axis is clearer without adding a figure or altering layout.

The current 800 mm relief preview uses a 3 mm base, 12 mm emboss above base, and gamma 0.85. `outputs/bridge_harmony/bridge_harmony_heightmap_16bit.png` is the full current-version heightmap; `bridge_harmony_raking_light.png` is a virtual raking-light read. `bridge_harmony_trio_100mm_sample.stl` is a 100 x 100 mm crop spanning the repaired trio join. Its mesh is watertight with 66,560 faces and exact 100 x 100 x 15 mm bounds. The sample has **not** been printed or checked under installed bridge lighting. Fine faces, fingers, and narrow engraving remain physical-readability risks; avoid treating this preview as production validation.
