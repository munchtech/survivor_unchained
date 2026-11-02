You are a medium solver for the Storybook 5 lead, owning plates p0, p1 and p1d, and p2 of SB00 (the ink lore intro), for fix round 3. Round 3 is the last judge round, so every fix must land clean at 1:1. Your final message returns to the lead.

First read `tools/storybook/briefs/sb5_solver_common.md` and follow it. Another solver is editing p3-p7u in the same files at the same time.

The latest frames are `tools/storybook/out/sb3_frames/r11/sb_sb00_<t>.png`, and the judge's 1:1 crops are in the scratchpad named in the common rules. Earlier solvers' scripts: `ink_sb5_ab.py` (p0/p2 patches) and `ink_sb5_p.py` (p1 forge, p1d, p5): read them first and extend them; don't start over.

## Fix list (judge r2; all show at 1:1). Coordinates are frame px at the named time.
1. **CUT the forge (the lead's decision).** The judge: the forge is "the most stock-AI plate ... a second illustrator", and its repaint left seams (4.0/6.5). Drop the forge and its sparks fx.
   - p1d now runs from 2.5 s to 15.5 s, opening with p1's current "in" (the light reveal from p0).
   - Camera: open high on the pit, with the legion's torch column on the steps at upper right in frame (the source is 1677x938, so there's about 230 source px of tilt at zoom 1.0 = 1.145x of the source px). Tilt down slowly to the door by about 8 s, then a slow push to no more than 1.2x of the source px by the slide.
   - Keep the slide (12.0-13.8 s) and the hard switch to shut on the 13.8 s drum.
   - Keep the lintel at least 40 px below the letterbox in every frame from about 8 s on (your script's assert).
   - Every cue keeps its absolute time. Check COVERS and PLATE_ORDER, so that no forge plate remains and nothing is left uncovered from 2.5 to 15.5.
2. **12.5: the sliding slab is drawn in front of the lintel** (its top-left corner at about (930,392), about 35 px above the lintel's lower edge at about y 430 there, hiding the runes at about x 930-1045). Mask the slab with the lintel's outline and the right jamb, so it passes behind both. Add a 6-10 px warm rim on its leading left edge (it faces the glow). Check frames at 12.2, 12.6, 13.0 and 13.6.
3. **The 13.8 s switch:** sell it as impact. Add a 3-4 frame camera kick (about 6 px) on the hit, plus a small dust puff at the slab base (the existing particle presets; never the smoke preset, which is a blob).
4. **17.0: p2's deep door** (about 400-970, 370-940) is a crude pale panel, a flat step down right after p1d. Replace it with p1d's SHUT gate seen deep in the rock:
   - composite the gate region of `out/sb5/p1_D2_shut.png` (jambs, rune lintel, slab, the chain across, the gold seams on all four edges), scaled to the dolmen's place;
   - run it through `ink_post` so it sits in p2's paper;
   - blend it into the strata with a feathered mask; darken it to p2's values so it's a deep, dark gate with warm seams, never a lit panel;
   - remove the hooked curl on the old capstone (about 850-950, 370-400).
5. **21.0, the story read:** the light must visibly reach the surface.
   - Make the threads' upward reveal/pulse plain in the 17-24 s span (the light travelling up the branches to the road and the hearth).
   - Repaint the green pebbles (about 1600-1900, 650-940) as dark stone, so only the warm ones glow.
   - The orange and green triangles read like candy corn: make the warm stones irregular lumps.
6. **p0, the hair tuft:** a pale tuft at (390-540, 140-250) at 0.8/2.0 sits under the letterbox with no head. Darken it to the cloak's value (or lower the plate about 60 px if that's cleaner).
7. **Optional, only if it's a one-line change:** p0's lit wash is dusty rose. Shift its hue toward gold/orange (about 30-40 degrees) so ember reads as gold.

## Shoot
Round `r12b`: FROM=0 TO=25.5 TIMES="0.8 2.0 4.0 6.5 8.0 10.5 12.2 12.6 13.0 13.6 14.0 14.5 17.0 21.0 24.5", under the shoot lock. Look at its half sheet once yourself, and fix anything plainly broken before you return.

Context budget: 200k
