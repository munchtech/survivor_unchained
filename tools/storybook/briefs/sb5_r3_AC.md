You are a medium solver for the Storybook 5 lead, owning plates p3, p3d, p4, p5, p6, p7 and p7u of SB00 (the ink lore intro), for fix round 3. Round 3 is the last judge round, so every fix must land clean at 1:1. Your final message returns to the lead.

First read `tools/storybook/briefs/sb5_solver_common.md` and follow it. Another solver is editing p0-p2 in the same files at the same time.

The latest frames are `tools/storybook/out/sb3_frames/r11/sb_sb00_<t>.png`. The judge's 1:1 crops are c822.png, c780.png, c805.png and c860.png in the scratchpad named in the common rules. Earlier solvers' scripts: `ink_sb5_ab.py` (p6/p7/p7u), `ink_sb5_c.py` (p3/p3d/p4), `ink_sb5_p.py` (p5). Read them first and extend them; don't start over.

## Fix list (judge r2; all show at 1:1). Coordinates are frame px at the named time.
1. **82.2 (gate NO), an inpaint seam.** The wet-stones patch ends in a straight vertical edge at x≈905, y≈815-940 against the water texture, and its pebbles are crisper and finer than the cloak and water around them. Fix:
   - break the patch's right 40-60 px into an irregular waterline, with carved ripple strokes curving under the flask;
   - lower the patch's highlights about 15% and soften the pebble detail.
2. **27.0 / 30.5 (gate NO), a crop.** The speared man's head is cut by the right edge at x≈1845-1920 (half a face, a glowing eye, the spear aimed at it) for the whole opening hold.
   - Move the opening framing at least 90 screen px left, so his head is fully out and the spear runs cleanly off the right edge.
   - If there's no room on the left (the dead hand at x≈215-300 must not hit the left edge), start the pan at 25.5 instead, so he comes fully into frame within the first second.
   - Also add a thin ember slit between the risen's lips (≈715-745, 255-262 at 30.5). Tint p3d's stray red sky dashes (39.0 near (1385,320), (1650,335), (360,215); 44.0 near (1415,350)) to the sky's navy or straw.
3. **p6 lamps (78.0 at x 1280/1355/1390/1500, y 375-405; 80.5 at x 1095/1165/1205/1315, y 370-400).** They are four identical teardrops with cream cores on vertical stems: bulbs on sticks. The "reflections" are the stems, standing on the bank rather than on water. Fix:
   - draw each as a small dark iron lantern or cresset silhouette, shapes varied, with a cold-blue flame and a ragged carved halo;
   - put the reflections ON THE WATER directly below each (80.5: y≈455-520), as 3-5 short broken horizontal strokes per lamp;
   - keep the reveal from behind the near hill.
4. **The p5 lamp is not p7's lamp.** At 57.5 (around 960,300) it's a closed ball cage with crossing straps; p7/p7u show an open bowl of horizontal iron bands with a handle arch and a ring on the chain, the flame rising from the open top.
   - Replace p5's lamp with p7's: cut the basket from p7's posted layer, then scale, tone and post it to p5's night;
   - keep the chain, the drip of light and the rings;
   - check it reads at 57.5, 63.0 and 69.5.
5. **p5's hand (56-71 s).** The palette and water are the film's, but the snow and banks are a fine speckle, the figures fine pen, and the only flat black mass is the water. Next to p7 it looks like a second engraver. Try POST only, on the p5 source:
   - thicken the dark line work about 2 px at plate resolution;
   - crush the mid-darks so the far banks (frame y 140-330) go flat black;
   - median the snow speckle (figures masked out) so it reads as carved strokes.
   Keep the dead faces, the cressets and the lamp exactly readable. If the result muddies, keep the current p5 and say so. No Krea, no ChatGPT.
6. **p4 jug** (55.0: x≈1000-1115, y≈228-335; 51.0: x≈1685-1795, y≈205-300). It's a soft brown smudge with a dark-red fringe, the only uncarved object at the focal point, and with no stream it reads as drinking. Fix:
   - re-carve it in the lantern's hand: a black keyline, 2-3 cut highlights, flat clay color, no fringe;
   - tip the spout down onto the lantern's top vent (about 1120, 265 at 55.0);
   - add a thin carved oil line (2-3 px dark gold) from the spout to the vent.
7. **p4 water** (47.5: x≈820-1400, y≈680-940; 51.0: x≈150-650 and 900-1100, y≈700-940; 55.0: x≈0-450, y≈740-940). It's still a speckled rose-mauve stipple, with sawtooth salmon "reflections" that mirror nothing. Fix:
   - carve it like the cool water on its own left (47.5, x≈560-900) and the owner's example: a dark navy ground and long horizontal cuts;
   - show the sky's reflection only as a few broken gold and orange strokes under the bright sky;
   - remove the sawtooth.
8. **80.5 silhouette (≈1520-1625, 600-860), mild.** Keep the rim only on the edges facing the lights (the hood top and the left shoulder), broken into carved strokes. Add 2-3 deep-blue fold gouges inside the cloak.

## Shoot
- Round `r12c`: FROM=25.5 TO=56, TIMES="26 27 30.5 35 39 44 47.5 51 55".
- Round `r12a`: FROM=56 TO=89.5, TIMES="57.5 59 63 66 69.5 72 75.5 78 80.5 82.2 84 86 88 89.2".
- Run both under the shoot lock. Look at each half sheet once yourself, and fix anything plainly broken before you return.

Context budget: 200k
