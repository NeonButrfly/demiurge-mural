# V10 anatomy and halo corrections

Tracking: GitHub issue [#13](https://github.com/NeonButrfly/gothic-image-repair-suite/issues/13). No milestone; this is a focused correction pass.

## User requirements

- Replace the entirely wrong upper demon arm with one coherent limb.
- Replace the incorrect lower-right reclining woman.
- Center the spiked halo behind the front angel's head instead of beside it.
- Remove the rounded bump below the angel's abdomen and restore continuous relief.
- Remove the highlighted bubble clusters in the upper-right background and replace them with angular wing and Gothic architectural relief.

## Preservation rule

Use the v9 raster as the destination and five independent masks. All pixels outside their union must remain byte-identical to v9. The original 2048 Demiurge source is a motif and anatomy reference, not a whole-image replacement.
