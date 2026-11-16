# Lane E: the art style nailed down for the demo (brief, 15 Nov 2026, written by coordinator #14 on Fable)

Read `tools/scratch/coordinator/briefs/wave1_15nov.md` "## Common" first (read "#13" as the coordinator who spawned you). Type `su-lead-high`, judged, own worktree from integration, branch `demo-look`. State file: a new TOP block in `docs/handoff/art_style.md`, kept current from your first commit. Its sheet (item 1) is the bar the other four lanes' judges use, so item 1 comes before everything.

## The owner (word for word)
15 Nov 2026: "and a big polish pass on getting our cell shader painterly overlay art style with vibrant colors nailed down"
19 Oct: "the 'correct' colors just somehow more vibrant". 4 Nov: "I want art to be...a big deal. not a patch." 3 Nov, on the demo: "it doesn't know what it wants to be stylistically. art wise it needs a style."
Read these as function, not literal (owner rule): "painterly overlay" = the frame reads as PAINTED; whether that is a screen pass or paint in the surfaces is yours to prove (item 5). "Nailed down" = one look, stated as numbers, on by default, and checked by a script, so it stops drifting lane by lane.

## Scope
The demo is ONE dungeon, the den (`hollow`), at the dungeon camera (62 degrees, 24 m; `godot/logic/Play/Zones/MapRun.cs:160`). The camera is never moved to match a target. Build and judge the look at that framing only (she is 40-60 px tall). Not yours: the den's painted set, its objects and floor (lane C, branch `dungeon-1`); skill effects one by one (lane B); armor meshes (lane D). Yours: the rules and numbers they build to, the grade, the light rig, and her, the foes, loot and effects as CLASSES in the frame.

## What exists (found 15 Nov; verify before you lean on a line number)
- Rules: `docs/design/LOOK_BIBLE.md` (14 rules; rule 4 "Vibrance, not saturation": color lives in the light, shadows keep color, skin protected, never a global saturation boost).
- Shading: `godot/shaders/cel.gdshaderinc`, `std_cel.gdshaderinc`, `kit.gdshader`, `fx_cel.gdshaderinc`, `vat.gdshaderinc` (foes), `heroine_*`, `woman_skin`; her line `hero_ink`, `hero_line`, `hero_line_hair` (ON). Rigs: `godot/logic/Look/Rigs.cs`, `rigs.json` (rig `den`).
- Grade: `godot/src/World/Atmosphere.cs` (AgX line 244, `Mute = 0.16` line 103, `--air-tune` keys lines 315-357, `--grade-try`, `--grade-off`), presets in `godot/logic/World/Atmospheres.cs` (line 40 `Saturation 1.0, Vibrance 0.2, Contrast 1.16, Toe 0.5`; `PaintVib`, `PaintShadow*` per preset; the `Den` preset at lines 74-80 is `Day` with a dark sky and fog, so the den has NO grade of its own today).
- Paint pass: `godot/src/World/Brush.cs`, `BrushEffect.cs` (anisotropic Kuwahara + stroke texture), OFF by default; dropped on 20 Oct as invisible at the play camera and +2.3 ms at 1440p. That test was before the cel model existed.
- Targets: `survivorsunchained_inputs\look_l1\g1\` (the owner's pick, 4 Nov; frame 10 is at play size), `look_l1\owner_ref_10nov\` (her, the play camera), the den's approved targets `survivorsunchained_inputs\gpt_den\`.
- Tools: `tools/style/` (`frames.py`, `palette.py`, `pairs.py`, `fx_measure.py`), `tools/look/` (`night_values.py`, `sheets_r2.py`); lead 26's in `survivorsunchained_inputs\look_l1\work\` (`pair_l23.py`, `her.py`, `shoot_l21.sh`: run `dotnet build godot` first). The den's shoot commands: `survivorsunchained_inputs\scratch_coord12\dungeon_state.md` top block.
- Parked, yours to take or drop with a reason: `rim-back@bce213a96` (a compute rim mask, CLOSE on its judge, suite not run).

## The fixed list, in order
1. **The demo look sheet, FIRST (send it to the coordinator before anything else; it goes to lanes A-D):** measure the approved targets and write, as a new section of `LOOK_BIBLE.md` ("The demo frame: the den"), the value band and the chroma band for each class: her skin, her plate and trim, her hair, foes, elites and the boss, ground lit and in shade, effects, loot, HUD accents. One rule and one number pair per class, and how to measure it.
2. **Vibrant:** shoot five den frames (her standing in a room; a pack fight mid-Sunder; Bladestorm in a crowd; the boss lair; a loot drop with the HUD). Where ours is under the sheet's chroma, fix it by rule 4: the den gets its own grade and rig numbers (`Atmospheres.cs` Den, rig `den`), and say whether `Mute 0.16` still earns its place. The den's round 10 failed as mauve and dark against warm brown targets: do not go there.
3. **Her:** the first read in every frame (the lightest, most colored figure, held by a dark line, a cast shadow under her), in today's plate; lane D's starting kit drops into the same bands.
4. **Foes:** two-band light, the line on everything that acts (rule 8), a stepped rim; readable on the den's floor, elites and the boss a step above.
5. **The paint read:** an honest A|B at 1:1 of (a) today, (b) brush in the surfaces (stroke breakup on the band edge and in the fills), (c) the screen pass at a cost you can defend (cap +1.0 ms at 1440p). Pick by your own look; if two are close, bring the coordinator the pair for the owner.
6. **Effects, loot, HUD accents:** fix only what is global (`fx_cel`, the `fx_p7` palette); the rest is rules handed to lane B.
7. **Lock it:** the defaults in data; `tools/style/demo_look_check.py` measures the five frames against the sheet and fails outside the bands; `LOOK_BIBLE.md` updated; the `rim-back` decision.

## The gate
Your own 1:1 look says bet on all five frames. Then ONE half-size sheet, ours beside the target, to the coordinator FOR THE OWNER (the owner sees it before any judge: "vibrant" is their taste). Then ONE max judge (`Item: demo-look`, `Effort tier: always-seen`). Not close after two honest passes on a frame: stop and bring the sheet. Suite: in `godot/tests`, `python ../../tools/quiet.py -- dotnet test`. Report: verdict first, branch@sha, suite, sheet path.

## Sharing with lane C
Lane C's color item aims at the same targets. Until your sheet exists, C uses its own numbers; after, C's grade moves to yours. You own `Atmospheres.cs` Den and rig `den`; C sends you requests through the coordinator. If `dungeon-1` is not merged when you start, merge it into your branch first and say so.
