# P7 TAKE 7: the held cut's stroke, the laying rebuilt (lead 9, 10 Nov; main's word: a rebuild from the judge's list, the spec fixed, build only)

One max solver, 160k. Worktree `.claude/worktrees/skills-p7`, branch skills-p7, start = the tip (51e5e21be or later).
Start pack, in this order, nothing else first:
1. `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_skills_p7\l5\facts_grip.md` (take 6 round 4: line map, keys, commands, what failed and why: items 20-24 hold for take 7 too).
2. ONE picture: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_skills_p7\l9\judge\sunder_d_cut0_1to1.jpg` (take 6 at 1:1, day, frames 302-313, 4 a row, unscaled 360x320 crops round her). Frame 304 (row 1, third tile) is THE MODEL FRAME: a tapered leaf with a gold combed tail. Frames 303, 305, 306, 307 are what failed (below).
3. The code by the line map: `godot/shaders/fx_grip_stroke.gdshader`, `godot/src/Fx/BattleFx.Grip.cs` (GripCut ~287, GripSet ~405, GripHead ~468, GripLay ~490, GripDraw ~570, GripContact after), data `fx_language.json` p7 `grip`, test `godot/tests/FxP7Tests.cs` TheHeldCutsStrokeIsACommaInThreeBands.

## Why take 6 failed (judge a685c6b68779ac243, max, CLOSE "a wide one", 18 of 22 full frames NO)
"From birth through the pressed frame it reads as a white flag or sail fixed to her sword."
1. The head IS the blade's line: a ruler-straight edge of 45-75 px on opaque flat white (303-307, 482-484, day and night). The pressed shape is a D or a sail.
2. The press does not read as pressure on bodies: the outer edge is a smooth clean curve, the peak lasts 1-2 frames, and the fat part TRAVELS with the blade (by 308 / 485 the place it pressed is already thin gold).
3. Birth: frame one is a chip or a squarish tag (302, 481); night cut 0 draws nothing at 303-304 and pops in at 305 as a 45x50 flag; day cut 0 starts under her, the other three at her right.
4. On the thinning frames the leading end is a squared cut of 15-35 px (308-311, 485-489); at 489 it is a straight spur at an angle to the arc.
5. Colour in blocks at the press: white, gold and amber stacked ACROSS the stroke with a near-straight boundary, and a step in the outline where white turns gold (484, 485, night 307).
6. Flat fill on every frame: one cream value; 310-311 / 488-489 a clean vector crescent.
7. Night: a paper cutout in the same cream as her ground ring.
9. Reach: the cut whitens bodies out to about 350 px from her; the paint reaches about 115 px.
(8, the sync of the bodies' whitening and the swell, is NOT yours: it closes with the chained cuts. Timing is never tuned to today's clips.)

## THE SPEC (fixed; a change of what the stroke IS comes to the lead as a line first)
What it is: ONE brush stroke of paint laid by the sword. One mesh, one material, one draw. No separate contact object in any form (four failed); everything below is the stroke's own silhouette and fill.

(i) THE HEAD IS A BRUSH CAP AHEAD OF THE BLADE. The stroke's leading end runs on past the blade's line along the path's tangent by a cap about as long as half to the whole of the stroke's width there. The cap is convex, slightly ragged (bristle tips: a hashed hard edge, a few px of variation, never a straight line, never a perfect arc), and the inner edge behind it is concave, so the pressed shape is a FANG or crescent. The blade's line is never an edge of the silhouette on any frame. The stroke's body stays exactly on the blade's path (keep: "the stroke sits exactly on the blade every frame"); only the cap leads.

(ii) THE PRESS IS LAID, NOT CARRIED. Each laid sample (rib) stores its own press (width share, whiteness) at the moment it is laid: the base profile, raised where the blade crosses the bodies (the contact). After that a rib's press only thins with its age (the shedding); it never moves along the stroke. So: the thick section STAYS where it was laid for 2-3 drawn frames while the head moves on, and the finished stroke is fattest at the contact zone and tapered at BOTH ends. Nothing is scaled by "distance behind the head" except the cap and the tail's taper.

(iii) THE BODY IS BRUSHED, NOT FILLED. 2-3 close values (not one cream) streaked ALONG the sweep, anchored to where they were laid (they do not swim as the head moves). Over the last three drawn frames dry-brush gaps open along the WHOLE length, so the last frame is mostly streaks (today only the tail tip combs). Colours interleave along the sweep: gold tines run up into the white and white tines down into the gold; no boundary across the width, no step in the silhouette where one colour ends. Hard cel edges stay (no soft alpha gradients, no glow).

(iv) THE CONTACT SPLAYS AND THROWS. On the contact frames the OUTER edge of the pressed ribs splays: 3-5 short tines and flecks rooted on the stroke's outer edge (fanned bristles), part of the same mesh and material. AND the paint reaches the cut's hit radius: thin streaks, rooted on the pressed section's outer edge, carry out to the struck bodies (as far as the sim's reach, `Ev.Slash.Reach`; the struck bodies' positions are in the hit events BattleFx already walks in the cut's frame; if they are not at hand in GripCut, throw the streaks radially inside the cut's arc out to the reach) and are shed in 2-3 drawn frames. They are continuous paint lines attached to the stroke, never detached specks (the spark rule stands: no specks come back). Their number follows the cut's DISTINCT struck (`tr.Struck` is distinct since 51e5e21be; today's crowd cuts sit at the size cap), a handful for a crowd, none for an air cut.

(v) BIRTH. Frame one is a short tapered comma (pointed start, round ragged head) and it grows without a jump. Every cut is born on its first drawn frame, by day and by night alike (find why night cut 0 drew nothing at 303-304: `grip.min_seen` 0.5 m seen is the first suspect; a stroke too short to show is drawn as the cap alone, already comma-shaped, never as a chip, a tag or a wedge with a flat end).

(vi) THE END. As the stroke thins, its head end closes to a point or a soft dab: no squared cut, no spur. The exit leaves no residue (keep).

(vii) ITS OWN WHITE. The stroke's white is a data colour of its own, not the cream of her ground ring (her ring is not ours and is not touched): by night it must not read as the ring's twin. Expose it as data keys (day and night if they must differ).

KEEP (the judge's list; losing one is a fault): the gold on the inner edge and the comb tines at the tail (308-311, 486-489); day 304's leaf; clean curved edges at 1:1 (no stair-steps, no aliasing, no forks); the stroke on the blade every frame; white, gold and amber reading on both grounds; the even thinning 308-311; the kink's mitre and run-out for a path that turns (the Oathblade's hold uses the same laying: it must still build and draw; its look is not judged now).

NOT YOURS (another helper, after you): the damage numbers' draw order above the paint; a warm cast of light on the ground and bodies at the press; the camera shake; the sim; `GripCut`'s struck logic.

## Rules
- BUILD ONLY: you do not run Godot, take no turn and shoot nothing. The lead shoots your commit and looks at 1:1; expect one correction list from the lead while you are warm. So reach a FIRST COMPLETE BUILD (all of i-vii, however rough) by about 110k of context, commit and report at once; do not polish blind.
- Verify what can be verified without the engine: `dotnet build` in `godot/` (0 errors) and `dotnet test tests/Tests.csproj --filter "FxP7|HitBudget|SlashFresh"` from `godot/` (15 green today; rewrite TheHeldCutsStrokeIsACommaInThreeBands for take 7 and add tests for every pure part you can lift out of the view: the per-rib press and its ageing, the cap's outline, the tines' count from struck). One dotnet command at a time, foreground. Shader text cannot be compiled here: read your GLSL twice (types, every uniform set from GripSet, no unused varyings); `0 SHADER ERROR` is checked by the lead's shoot.
- Keep `--grip-say`'s lines (`grip cut frame`, `grip contact frame`, `grip end frame`, `grip ribbon frame`): the shoot script greps them. Add what take 7 needs (per frame: ribs laid, the press's peak and where, tines).
- Numbers live in `fx_language.json` p7 `grip` with a `_doc` each; dead take 6 keys and code are DELETED, not left switched off.
- Patch scripts go to files (bash heredocs with backticks break): `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_skills_p7\l9\`.
- Never `git stash`, `git reset --hard`, `git checkout .`; stage your files by name only (untracked .uid / .import churn is not yours); kill nothing; delete nothing outside your own edits. Commit as you go (WIP is fine, say so) and push.
- At the end REWRITE `...\scratch_skills_p7\l5\facts_grip.md` for take 7 (line map, keys, commands, what failed and why 1-24 kept in one line each + yours, unlooked / open): the next helper reads it instead of the code.
- If you have not started editing by 60k, stop and report what blocks you.

## Report (your final message; no report file)
The sha; what the stroke now is, in the spec's (i)-(vii) order, each DONE / PARTIAL / NOT with one line; what you could not verify blind and what you would look at first in the frames; tests' numbers; the keys added and removed; your token use.
