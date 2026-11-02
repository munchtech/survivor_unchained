# Handoff: skills look and feel

## Combat VFX 10 (vfx-7, 2 Nov): item 2 MR READY (her auto-attacks); item 3 (Warden skills) next
**Item 2, her auto-attacks** (SKILL_VFX_STUDY.md §6 item 2): r3 max (the FINAL round, cap raised to 4 by main) said **PASS-WITH-NOTES on all four and ship as a net gain**, with its 5 safe cuts applied (7deaa78a6). History: r1 FAIL (sweep medium, Disc and Bash far), so the sources were rebuilt; r2 FAIL medium on all four; r3 PASS-WITH-NOTES (sweep, hit kit and Bash close; Disc medium by day, close by night).
- **What ships:**
  - Sweep: a true gold crescent, peaking at f2 and eaten from its trailing horn, on real frames through the hitstop (oath_sweep.gdshader).
  - Hit kit (HitKit.cs `HitKit`, `StruckRimOn`):
    - a 2-frame flash at 15% then 6%, with none on the Bash's stunned (`rimNoFlash`);
    - a #FFB84A fresnel rim fading over 8 frames, 0.55x at night;
    - sparks 3-5 per body on at most 6 bodies a swing;
    - solid lit chip puffs (day life x0.7);
    - the bone-chip "snow" skipped for her auto-attacks.
  - Disc (disc.gdshader `halo_gain` x0.6 by day): twin world-space rails, steel band glints, an amber 1.3x halo, a 2-frame contact flare.
  - Bash (bash_wedge.gdshader + new bash_wall.gdshader):
    - forward-weighted 100/50/7% at 0/35/69 deg over the sim's real ±1.2 rad, 3.4 m (wider than r1's spec on purpose);
    - a bronze flash at the shield face and a 0.42 m standing front;
    - a brown plow and a gold stun twinkle;
    - a view-only throw for the dying (CrowdView), 1.7-1.8 m by f15.
  - Sim untouched. The "shield_bash N" debug line is now only shown with `--reflex-note` (aa96dcae0).
- **Known (r3 judge, closed):**
  - Sweep: a moon-even taper, one flat gold, reads thin in a dense crowd; a dark olive inner band on f1.
  - Hit kit: the f1 sparks read white; the puffs are paler than the road; the flash leads the arc by 1 frame.
  - Disc: no spin reads by day at 1:1, and the rails are a faint V.
  - Bash: the rim reads smooth; toward the camera the cream band thickens; the plow is faint by day; the throw-back only reads in motion.
  - Night: s3's hit cluster is a dense glitter.
  - **"Not yet effortlessly badass: the sweep needs weight, the disc a sense of speed: a design pass, not values"** (a later list item, owner's call).
- **Tests and perf:**
  - Tests 1373/0/10.
  - Release ABAB at night, 250 horde, `--aa-fx-off` (A, none of the kit drawn, sim the same) vs on (B), window 8-10.5 s while the crowd is dense (`survivorsunchained_inputs\vfx10\perf`):
    - B-A mean is CPU +0.10/-0.02 ms and GPU +0.10/-0.02 ms;
    - p99 is +0.9/+1.1 ms in pair 1 only (likely the first-use pipeline compile; pair 2 is -0.03/-0.12);
    - this is the whole kit against nothing, so an upper bound on the change.
- **Shots:** `survivorsunchained_inputs\vfx10\aa4\r3c\sheet_{day,night}_half.jpg` (the final build; the judged r3 set is `aa4\r3`). The day `d_open` beat never fires (the crowd is too dense). Shot scripts and stats: session 14076147 scratchpad `vfx10\` (shoot.sh, sheet.py, perf_stats*.py).
3c\sheet_{day,night}_half.jpg` (the final build; the judged r3 set is `aa4
3`). The day `d_open` beat never fires (the crowd is too dense). Shot scripts and stats: session 14076147 scratchpad `vfx10\` (shoot.sh, sheet.py, perf_stats*.py).
- **Dev flags:** `--aa-beats`, `--aa-norim`, `--aa-pool K`, `--aa-fx-off`, `--reflex-note`.
- **Cost:** item 2 ~1.45-1.5M of the 1.45M cap (r2 solver ~0.2M + judge 0.105M; r3 solver 0.21M + judge 0.12M + runner 0.03M; lead ~0.12M).

**Next: item 3, the Warden skills** (`docs/design/WARDEN_SKILLS_VFX_HOOKS.md`). Hooks a/b are in integration (art keys `rebuke`, `watch_bell`, now in the `nova_holy` case of BattleFx.Skills.cs, to split out; `Ev.Barrier`). Sunder and Groundbreaker too.

## Combat VFX 9 (vfx-7, 2 Nov): MR READY. The Long Cut rebuilt; her auto-attacks next
**The Long Cut** (round cap raised to 4 by main; the last round). The max verdict on (B, "once she has the pose") was FAIL CLOSE, and the judge's final cuts are applied. What ships: the press (local gold light, white-gold blade core, no exposure lift or sepia), the hold, the fuse run, the cooling, the smoke curtain, both scars and the clear field. r1 was FAR, r2 and r3 were MEDIUM, r4 CLOSE.
- **Sources:**
  - `tools/fxsim/longcut_crack.py --seed 7` bakes the crack strip (`godot/art/fx/longcut/crack_*`, `crack.json` with the centre line);
  - `tools/fxsim/longcut_chunks.py` (Blender) builds `chunks.glb`;
  - `tools/fxsim/dust_sim.py` + `pack.py` make `fb/lc_dust` (built, but the jets are CUT: `JetsOn=false`).
- **Code:**
  - `FlareFx.LongCut.cs`: beats, ResolveDooms (two death classes timed from the drawn crack, fuse arrival + 0.1 s/m), the jets, smoke and chunks;
  - `FlareFx.LongCutLight.cs`: press, hand, rim, sweep, the Spend column, the light dip;
  - `FlareFx.LongCutArt.cs` reads the PNGs from the project folder, so **a shipped build must pack them**;
  - `flare_world.gdshaderinc` (the seam sampled in the ground shader, the sweep band, the scorch) and `vat.gdshaderinc` (char and ash);
  - `CrowdView.FlareCorpseAsh`;
  - `--no-spawn`.
- **Cuts behind consts:**
  - `FL_LC_FRESH_CORE 0`: the fresh seam has no white-hot stage and opens at its orange stage;
  - `LcGoldDead=false`: no gold cracks or edges on the struck; all die as lit char then ash;
  - `LcSweepEdgeLights=false`;
  - `JetsOn=false`.
- **Bugs found:**
  - The blade lookup `"arm:*"` never matched, because Godot turns `:` into `_` (now `"arm?*"`). **The Arcanist's `FindChild("arm:mage_staff")` likely has the same bug** (unfixed, not ours).
  - The vat night factor read the sweep gain (gold was negative light by day).
- **Frozen times** (Animation 59 is authoring her clip to them): press 0, sweep ~0.20 for 0.35 s, cleave ~0.545, cool 1.95, dead 6.1.
- **Known (r4 judge, ranked):**
  1. the sweep still reads slightly as a ray (now clamped to 12 m), and its afterglow doesn't read;
  2. no shadows swing away from the line;
  3. no white-hot instant on the fresh seam (cut);
  4. day ash deaths leave dark brown smudges for ~1 s;
  5. the night b6 crack fill is pale.
  
  Out of scope: auto-attack sparks and haze at night b1-b3 (item 2), the night loot ember ring b8-b9 (loot), and the LEVEL banner (UI).
- **Shots:** scratchpad b9e8a09f `vfx9\cuts\shoot_lc.sh day|night` (+ measure.py, half.py). Final frames are in `survivorsunchained_inputs\vfx9\lc_final\`; judged frames in `lc2`, `lc3d` and `lc4b`.
- **Tests and perf** (MR, 77c2fed74 plus docs):
  - Tests 1373/0/10. The import logs one benign error line.
  - Release ABAB at night with a 250 horde (`survivorsunchained_inputs\vfx9\perf\lc_A3..B4`), B minus A from the press to the cleave:
    - CPU mean +0.16 ms;
    - CPU p99 +5.6 ms: a one-frame ~11 ms cast spike, KNOWN (extend the warm-up);
    - GPU mean +0.08 ms;
    - shadow draws +23.
  - The aftermath is about even.
- **Cost:** VFX 9 ~2.1M; the Long Cut over VFX 7-9 ~3.05M.

**Next:**
- **Item 2, her auto-attacks** (study §6 item 2): the Oathblade sweep crescent and the Judgement Disc, a shared hit kit. First check that the Disc and Shield Bash fire in that loadout, and the ~4.5 s stop after a Flare.
- **Item 3, the Warden skills** (`docs/design/WARDEN_SKILLS_VFX_HOOKS.md`): cherry-pick classes-17@426ce9d64 (hooks a/b: `rebuke` and `watch_bell` art keys, `Ev.Barrier`). Split those two keys out of the `nova_holy` case in BattleFx.Skills.cs. Icons are UI's.

## Combat VFX 7 (vfx-7, 2 Nov): HANDOFF. The Long Cut r1 FAIL far, rebuild from better sources
**The owner (1 Nov):** "Yes, Long Cut first". Build item 1 of `docs/design/SKILL_VFX_STUDY.md` §6 (the seam of morning, FLARE_LOOK §3 lines 289-311) with the Warden's dawn-gold press motes folded in. Item 2 (her auto-attacks) is next but NOT approved to build; its gap is confirmed (study §3). Judges at max, day and night, whole-frame gate first; perf in a packed night crowd; round cap 2-3 (1 used).

**Done:**
- Study: `docs/design/SKILL_VFX_STUDY.md`. `SKILL_VFX_REFERENCES.md` now carries the numbers 1-11, matching CLASS_IDENTITY (that doc was already right).
- Ref sheets: `survivorsunchained_inputs\vfx_refs\<id>\peaks.jpg` and `bursts.jpg`, made by scratchpad `vfx7\refsheets.py`.
- Build r1 (5ff2bef01, tests 1337/0/10), on a procedural route:
  - `godot/src/Fx/Flare/FlareFx.LongCut.cs`: press motes off the blade, gold head light, sweep light, the fuse light at 60 m/s, dust, chunks, sparks, smoke, the struck burn-up timed to the sweep angle or the fuse.
  - `flare_world.gdshaderinc` gets the globals flare_seam, flare_seam_t and flare_sweep, registered in project.godot.
  - `vat.gdshaderinc` gets a ragged gold burn-away.
  - `CrowdView.FlareStatueLook` + `FlareFx.StatueLook`: the frost-blue flash was Burns Twice's `frozen=1` on every Flare's statues.
  - The beat shots b4_sweep..b8_smoke.

**Judge r1 (max, ~100k): FAIL, FAR.** All 14 frames fail the gate. Only the day crack's shape and its gold-to-red cooling land. Missing:
- the press answer (the drain reads cold grey);
- the sweep (invisible);
- the fuse travel (the beats are mistimed);
- death in gold (a black radial star of corpses stays; the judge won't accept "harness" without a respawn-off reshoot);
- the scar.

At night the seam reads as a straight tube with banding, and ~100 ember orbs bury the cool-down. Full verdict: transcript a08842844413e91d7. Its ranked fixes:
1. Die in gold, then gone (rim 2-3 frames, char-dissolve to embers 0.6-0.8 s, removed). Reshoot with respawn off.
2. A gold instant press (a warm 4 m light, bloom pulse, rim on her and the blade); the hold drain warm, never grey-cyan.
3. A visible sweep: 0.3-0.4 s, a warm ground wedge, a fading wash for 0.5 s, a dust skirt, no rim.
4. A crack with depth: taper 30-40 px to 10 px at 1:1, dark lips, 8-15 raised chunks, a meander, a chain of low warm lights so the shadows swing.
5. Night: cap the core's emissive; the glow comes from the ground lights.
6. Real dust and chunks, not confetti.
7. Hold or shrink the ember orbs until after the seam.
8. A warm exposure lift of ~1.3x for 2-4 frames at the cleave, a shake, and a char scar for 3-6 s.

**Next (scrap rule: far means rebuild the sources, not patch):**
1. A medium solver rebuilds the crack from a baked source (a Blender crack mask/decal with charred lips, taper, meander, plus rock-chunk meshes) and the dust/smoke as a tools/fxsim flipbook, Burns Twice's pipeline. In the same pass it does fixes 1-3, 5, 7 and 8 in code.
2. Reshoot with respawn off (find the lab arg) and real beat times. b4 at night came out before b3: check the Shots.Want times in LongCut.
3. Max judge r2, then a perf run without `--shot`: r1's 36/25 ms means include PNG saves.

**Routed (not ours):**
- Combat: after the Long Cut her auto-attacks stop ~4.5 s. No Ev.Hit at all: sim, not view. Likely nothing left in reach; check against Burns Twice.
- UI: "Barrow Dust" nameplates over ~30 enemies by day; the LEVEL 3 banner sits over the fight.
- Combat: a night wave spawns as a still ring of glows for 3 s.
- Burns Twice: its burn front is a screen-wide hoop, and the fireball peaks at 1.6x (~0.1-0.2M, later).
- Character: the arcanist mesh logs 0 shadow casters.

**Shots:** scratchpad `vfx7\shoot2.sh`; the recipe is in this file's git log and in the study. The press lands at 6.35 s; frames come ≥0.13 s apart. Frames: `survivorsunchained_inputs\vfx7\` (now = the hub, useless; now2 = real fights; lc = r1). The worktree's modified `.import` files are reimport noise; don't commit them.

**Paused here (VFX 8, 2 Nov):** not started. Merged integration 7472253fc into vfx-7 (junction removed and remade to the worktree's own public/assets). Next: the rebuild solver, step 1 of "Next" above.

**Cost:** VFX 7 so far ~0.95M (study ~0.45M, build r1 ~0.24M, judge ~0.1M, lead).

## Combat VFX 6 (vfx-6, 1 Nov): MR READY. No chevrons on round marks
**The owner (29 Oct, verbatim):** "the chevron on the circular telegraphs is not wanted, it dosn't look good".

**Built** (`godot/src/Fx/MarkPass.cs`, `godot/data/mark_look.json`, `godot/src/Fx/BattleFx.cs` ConeMark):
- A pattern "none" (id 6 in `PatternIds`). mark_look.json `"patterns"` maps circle, ring and cone to none. The default stays chevron, so only lanes carry chevrons: a lane has a direction, and a round mark's chevrons are zigzags on arcs.
- The bed has an unlit floor, `bf` 0.2 (as seen: the brightest channel on the display; `want = max(k x ground, bf)`). Before it, a night mark out of the lamp was only its rims, a hollow outline. Day is unchanged.
- Cones fill from their point, with a cast line, as discs do (`ConeMark(..., progress)` for hostile blows; shader fill for `kind <= 2`, gated inside the wedge).
- Salmon is unchanged.

**Judged (xhigh, 2 rounds, ~145k):** r1 FAIL close (the night cone and disc were hollow without the chevrons). r2 PASS-WITH-NOTES: every frame passes the gate, day and night, at the boss clearings, the arena and the town.

**Later list (not gating; added to the projection list below):**
- Where a lane fan's lanes overlap at the root (Red Hand's Volley), the chevrons cross into a lattice. Fade the chevrons in over the first 1.5 lane widths, or draw them only where one lane covers.
- At night the fill sits only ~1.5x over the bed's inner edge (~2x by day). The fix if touched: lift the night fill to ~sRGB 100,42,24.
- A lane end runs past a wall top onto a building (same family as the cliff jog): clip where the ground steps more than ~0.5 m.

**Routes:** Lighting: the night arena ground crushes to pure black outside the lamp. Character art: the Red Hand reads as flat, unshaded orange. UI: the bronze HUD statue goes semi-transparent over red lanes (05 in r2), so check the fade is intended.

**Shots:** `shoot2.sh` kinds bpack, bred, bdead (arena bosses at night: `--zone arena --boss boss_X --minute 29.9`) and mpack, mred (day: `--zone map --people X --at boss --time day`). Barrow knight and the crowd make lanes only. Backed up in `survivorsunchained_inputs\scratch_vfx6`; judged r2 frames and a 2x2 sheet (night cone, night disc, day cone, day disc) in `survivorsunchained_inputsfx6`. Tests 1335/0/10.

## Combat VFX 5 (vfx-4, 29 Oct): MR READY. Chevrons, and the owner picked B SALMON
**The owner picked chevrons (verbatim):** "agreed, chevrons - with clear edges and a flat line end not the arrow. clear cast line and edges".
**Then the color (verbatim):** "B salmon." It is set in mark_look.json (`"look": "salmon"`). The fire tint stays off.

**Built** (all in `godot/src/Fx/MarkPass.cs` and `godot/data/mark_look.json`; red marks only):
- Chevrons are on every red mark (`"patterns"` default chevron). The other patterns stay as named choices.
- The chevrons are cut dark into the bed ahead of the running front and lit behind it (`cd`). The bed's darkening is applied after the fold's cap; before it, by day, it was lost.
- Chevron shape: period `cp` 0.55 m, slope `cs` 1.5 (an apex near 67 deg), half width `cw` 0.06 m.
- The lane's far end is flat (`cap` 2).
- Clear rims: less outer glow (`eg`) and less bleed (`ew`), plus a keyline just inside them (`kg`, `kw`).
- The cast line is a hard line at the running front (`fl`, `fw`, `front` 0.04). It rides the pattern's light, so by day it can pass the red's fold as a pale line.
- Scarlet's look (`looks.scarlet`): `bo` 0.82 (bed opacity), `cd` 0.72, `hl` 0.5. Salmon keeps the defaults.
- School tint (`"tints"`, shader `pcol` code = pattern + 8 x tint): OFF behind `"tinted": false`. The judge would leave it off; it's on the owner's sheet as an option. `MARK_TUNE=tt=1` forces it for shots.

**Judged:**
- Round 1 (xhigh): salmon PASS; scarlet FAIL by day, close.
- Round 2 (xhigh, the last round): salmon PASS, every frame gate YES. Scarlet PASS on every frame except f14, a late Warden disc on the bank that is cut by a straight chord with no rim.

**Later list: telegraph projection** (pre-existing, routed by main 29 Oct; one item for the next VFX slot):
- The f14 chord: the height gate (g0/g1) on a sloped bank.
- The mark paints corpses and debris on the ground.
- A lane appears to jog where it crosses a roofless building's wall.
- A faint dark lane outlives the red for a moment after the hit. It seems to be BattleFx's own Danger decal bed fading out; unconfirmed.

**Owner sheet (SENT via main):** `C:\Users\munch\Desktop\survivorsunchained_inputs\vfx5\telegraph_color_scarlet_vs_salmon.jpg`.

**Next:** merge (main). Then the queued input below (the warden's 4 new skills), and the projection later list above.

The shot scripts (shoot.sh `NAME:LOOK:KIND:MARK_TUNE`, pace.py, jsheet.py, red.py, owner_sheet.py) are backed up in `survivorsunchained_inputs\scratch_vfx5`.

## QUEUED INPUT (28 Oct, from Classes 15 P6, via main): the warden's 4 new skills need VFX
Sim lands with placeholder art keys (classes-15; MR1 = P5b+P6). All warden-only, holy + steel. Build after MR1 merges.
1. **Sunder** (greatsword grip): slow heavy 220-deg cleave (300 with Wide Swing). Every 4th swing (3rd with Third Blow, 2nd with its Turn) a heavy overhead splits the ground in a line 7 m long, ~1.2 m wide, ahead of her; Burning Edge = holy fire along the crack. Her greatsword prop + clips are Phase 3; until then it swings whatever she holds.
2. **Groundbreaker:** every 5 s a crack races from her to the densest pack within 10 m (14 with Fault Line); the end heaves ~2.5 m round, 0.6 s stun. Twin Cracks = two cracks splayed 30 deg; Upheaval = lesser things popped airborne 0.8 s; Turn "Aftershock" = the same spot heaves again 0.8 s later.
3. **Rebuke** (reactive, no cast): each block strikes the blocker + 3 nearest with holy light, shield to targets. Turn "Shield of Morning" = a barrier glint to her per creature struck.
4. **Watch Bell:** every 6 s a bell toll rings 8 m round (10 with Loud Bell); everything drawn in to her for 2 s (draw-in streaks), she gains barrier (shimmer) per creature. Iron Bell slows what's drawn. Turn "Stone Bell" lays wall stones as it tolls.
**Generic Turn looks (parameters on each skill's look, not new art per Turn):** Pulse = fires 3x at 85% size, 0.3 s apart; On-kill = fires again from a corpse at 30% damage; school Turns recolor (fire/frost/holy); Wide/Linger exist (P5a). Turn names are placeholders for the story lead.
Owner standards apply: every press visible; Flare "BOOM" scale is for Flares, not these (keep these readable under a Flare).

## MR READY (Combat VFX 3, vfx-1, 28 Oct): the red line re-tint (MarkPass) ships; after the merge, the next lead starts at step 2 below

**Judged and done (all on vfx-1, tests 1191/0/10):**
- **The shot args (the r5 runs that made no frames):** not a code bug. The runs had dropped the lab spawn: elite shots need `--lab --auto on --horde 1:barrow_knight --dist 7 --spread 2 <look> --on elite`; the grave caller `--horde "1:grave_caller!,4:legionary,8:risen"`; the Prologue's Warden over the river via `pace.py` (STOP="pace stage Victory", `--on elite,boss`). Scripts with the working args: `survivorsunchained_inputs\scratch_vfx3\` (r5.sh, fb.sh, pace.py, m3.py).
- **Max judge r1 (A = re-tint, B = edges-only, one round):** SHIP A everywhere. Day ("ground stained scarlet, not cellophane"), water, teach, Knight, arena, hits, crowd, raise ring PASS-WITH-NOTES. B rejected (it kinks at the bank too; its night Knight lane fails the gate). One FAIL (close): the Warden's charge lane folding at the river bank + pink grass tips. `MARK_TUNE bed=0` still gives B for comparison (f44f6a0e).
- **Bank fix (bc43ef3b, a medium solver):** the "crease" was the shore foam re-tinted at its own value: the bed now takes a blurred value (8 px tile pre-pass, mode 0) within ~0.25 m of the water line; height-test slack scaled by the grid's bend (zero on flat ground); a soft fade on steep faces (0.9-1.4 m/m of the height grid); partly-gated grass tips pushed to scarlet. **Xhigh judge r2: SHIP** (01-06 gate YES; no regression on water or land). GPU 0.069 ms (was 0.041).
- Earlier (VFX 2): `godot/logic/Sim/TelegraphRead.cs` (elite+boss blows = Danger, crowd = Amber), the MarkPass compute pass after the transparent pass (AgX display chain, bed = scarlet at 0.82x the ground's SEEN value, water via `Water.Level`), crowd/raise amber #ffbc30, raise ring breath. Env: `MARK_TUNE`, `MARK_PASS=0`, `MARK_TIME=1`.

**Later list (judges' PASS-WITH-NOTES, only what shows at 1:1):** fill front reads as a seam on day/dark dirt (02, 03, 08, 09 of r1: make it a bright bar 1.5-2x the rim with a short glow, filled part a step brighter); rims weak in full sun (scale with the ground's brightness); lane end inside a house fades as a smudge (cap it); raise ring's taupe interior (drop its re-tint or lift to warm amber); Knight hit flash/blood barely reads on his pale body; a pale stone part under a lane end gets a red cap (treat rocks like the grass tips); arena frames are near-black ground (not ours: env/lighting).

**Next:**
1. Main merges vfx-1 (only MarkPass.cs since integration 3ef34f61; no art). Remove the junction first when merging in this worktree (README).
2. (After the merge) study docs/design/SKILL_VFX_REFERENCES.md + `survivorsunchained_inputs\vfx_refs\<id>\sheet.jpg`; write what our skill VFX take from them.
3. The Warden's 4 new skills' VFX needs from Classes Phase 1 (via main). Memory flare-is-a-boom-button for Flare looks.
4. The later list above, one judge round, when there's a slot.

**Known, not ours:** "3 RID leaked" at exit. Routed to UI: F7's "line" word orange; crit numbers over the hotbar; card ghost text. No flag to strip her lightning crit for hit shots.
**Cost this session:** max judge ~149k, xhigh judge ~59k, medium solver ~172k, lead ~120k; $0 API. 15 colliding .uid files from VFX 2 are in coordinator scratch f22ca2bc `vfx2\uid_backup`.

## Combat VFX 1 (vfx-1 worktree, 27 Oct): PAUSED at the coordinator's wind-down; judge round 2 next

**The owner's ask:** "a combat VFX lead (the Knight's salmon red line and white flash)". The coordinator's ruling: red for elite and boss blows only; the crowd's blows stay amber.

**Causes found:**
- **The Knight's line was never red.** Every hostile blow used `Palette.TeleBlow`, amber #ff9a1a. Elites were scaled to x0.28 and drawn as an additive emissive decal at energy 2.5. The AgX tonemapper folds that bright orange to salmon, and adding light over lit dirt turns pink.
- **The white flash** was `vat.gdshaderinc`'s struck term: hot^4 x0.38 plus rim^2 x1.1, a flat warm-white wash. From the play camera most of a body counts as "rim", so it became a flat cream cut-out, held through hit-stop.
- **The Grave-Caller's raise ring** (Ai.cs, Ring with Inner 0) drew as a filled 7 m salmon disc.
- **The Ford-Warden's cleave and charge marks** (Prologue.cs, about lines 787 and 795) never set `Boss`, so they drew in the crowd's amber.

**Built** (branch vfx-1, commits 748f462d, c336a847, 6cf7e3c7, 23461218, 312e8a4b):
- **The danger mark** (`BattleFx.cs`: `Ground`, `DangerOf`, `FillStyle`/`FillTexture`, `BedOrm`, `OverLane`; `Palette.TeleDanger`, `TeleAmber`): a scarlet edge pre-skewed for AgX over a near-solid old-blood bed, with its own hot running fill, NormalFade 0.6, crisp ring rims sized in metres, and an over-copy in the same shape.
- **Crowd blows and the raise ring:** dim true amber with a faint bed.
- **The struck flash:** a champion lifts its own paint, warm, with a rim pop scaled by the paint. The crowd's rim-only path is unchanged.
- **A dev switch:** `--on elite` frames each elite or boss mark (`tele<id>`), its hits (`hit<id>`) and one crowd mark every 6 s (`crowd`) (`Game.EliteShot`).

**Judge state:**
- Round 1 (xhigh) FAILED the line (it read coral/rose) and the other marks (the Warden's salmon, the Grave-Caller ring too loud). The flash got PASS-WITH-NOTES: the glitch is gone, but the crit lift was too weak.
- The round 2 build is measured but NOT judged:
  - Night Knight bed (119-154, 32-44, 35-46), saturation 0.75, hue 358-359.
  - Day bed brick (115, 48, 44), saturation 0.6.
  - Raise ring rim (203, 146, 78), hue 32.
  - Under AgX no red reaches (235+, <50, <40); the solver's offline curve gives (213, 73, 48) at 1.0.
- **Open:** the Warden's lane over the RIVER still reads rose (hue 347-355). Water writes no depth, so the decal lands on the riverbed under the water and the over-copy never fires. That needs a water-aware over-copy (a solver item).

**Next:**
1. Run the logic tests. Prologue.cs changed and they haven't been run.
2. ONE xhigh judge, round 2 of 3, on the r2 frames in `godot/.shots/`: `r2pro_teach_red_line_1`, `r2pro_tele32_3`/`_15`, `r2arena_tele0_2`, `r2day_tele0_4`/`_6`/`_8`, hits `r2pro_hit32_1..3` and `r2arena_hit0_1..3`, raise `r2pro_tele29_1..3`, Warden `r2pro_tele301_30` and `r2pro_tele302_10`/`_40`, crowd `r2gc_crowd_1`.
   - The judge's first brief and its verdict's levers are in this page's history.
   - The shoot scripts (`shoot.sh`, `pace.py`, `sheet.py`) are in coordinator scratch 7ccc6e14 `vfx1\` (and `vfx1\r2\measure.py`).
3. Fix the river case if the judge wants it.
4. Full test, then the MR.

**Asides from round 1 for other owners:**
- Crit numbers land over the hotbar (whoever owns the numbers).
- F7's "line" word is amber while the line is red (UI).
- No blood flecks on the Knight in the prologue (undead?).

**Later (coordinator):** the owner's 9 skill-VFX reference videos are downloaded (owner OK) to `C:\Users\munch\Desktop\survivorsunchained_inputs\vfx_refs\<id>\`: video.mp4, title.txt, 14 evenly spaced stills and sheet.jpg each. Scene detection found almost no cuts, so the stills aren't picked at effect moments. Study them after the MR.

**Worktree notes:**
- `public/assets` has the main checkout's 811 untracked asset files COPIED in, and the import was done.
- `git status` shows reimport noise on `.import` files. It isn't ours; never `git add` it.

For the next skills lead. Read in this order:

1. `docs/team/README.md` (the bar, how we work, heavy work takes turns).
2. `docs/team/RESUME.md`.
3. This page.
4. `docs/team/skills.md` (status, what is seen and what is not, the judgements waiting).

Branch: `worktree-agent-ad059388f00c19f9f` (pushed). Merge `origin/claude/vigilant-galileo-l6jqyx`
into your own worktree, then this branch if the main session hasn't merged it yet.

## The owner's words

- "we are striving for perfection". "AAA standard". "I don't want to polish, I want to create
  perfection." "Do we have soul?" Never settle: remake rather than skip.
- "leveling up all our skills ... leverage our gpu as always to create amazing effects and be
  careful of crop/squaring issues". Judge at full resolution, in a packed crowd.
- On loot (relayed): the old beams were "solid pastel tubes"; the Legendary's "a huge solid cream
  bar slanting across the screen". Lights must read as light, not geometry.

## The brief

You own how every skill looks, sounds and feels in play: arts, auto-attacks, evolutions, unions,
blessings, her rise, the enemy's verbs, loot's light (LOOT_DESIGN.md §8), and the story's looks that
combat asks for. Each skill must read at a glance in a horde, keep its school's colour and shape,
land every hit, and grow with rank. Combat owns mechanics and numbers: propose, never make them.
Batch shots in one Godot turn and look once. Krea only through the `gpu` turn (the face lead uses
it a lot: queue fairly). Commit and push at milestones; open no PRs. `dotnet test` (in
`godot/tests`) before every commit. Hand off at about 500k tokens.

## The main session's rulings (applied)

- Elites are capped too: two flash white at once on top of the three ordinary bodies.
- The Legendary's night foot glow about 180 px (measured 196, from 328).

## Done this round (all seen at 1920×1080 unless marked)

- **The night won** (`Ev.Victory` in `BattleFx.cs`): one ember-amber shaft with motes riding up it
  (`loot_beam.gdshader` kind 7's parameter is now its motes), a warm flash. Its foot fades over a
  breadth that goes with its width (it ended in a line across her feet). *The foot change is not
  yet seen.*
- **The way out** (`BattleFx.Story.cs`, `WayOut`): the cream hoop round her was ArenaRun's pulse,
  drawn as a holy-gold decal band. Now loot's batch draws a soft cold-blue band (kind 8) that comes
  2.4 s after the fall, as its prompt does. *The band is not yet seen at full strength (won5 queued).*
- **A chest's column**: seen, a soft gold shaft (fine; its core goes a little cream).
- **Moonbrand**: crescent glint at the hand (was a lilac sigil every cast); the brand silver on a
  dark bed with violet jets (moonfire tongues are now the pack's crisp `muzzle` jets, not its
  smoke-soft `flame`s); thinner trail; moonlight is silver-blue, moonfire deep violet.
- **Firepot** (`PotBurst`): crack, flame jets turned along their way on the screen
  (`Spin = atan2(-sx, sy)` from the camera's basis), burning powder, clay sherds, char smoke, a
  small heart.
- **Ticks are no blows** (`Enemy.LastDot`, view-only): no white flash, no flinch.
- **A slow is not frost** (`Enemy.HeldUntil`, view-only): a non-frost ground's hold draws no rime.
- **Fed deadfalls** (`BattleFx.Story.cs`): flame along the trunk (fire_wall cards pressed to a
  line), embers, guttering smoke in the last 4 s, a rush when fed. `--lit S` lights them S seconds.
- **"His age" / "She missed"**: the wolf's breath smokes in pale puffs with each pant.
- **Unions**: Frostfire Comet's own art `frostfire` (ice heart, frost tail, half-flame half-frost
  burst with ice round its rim, burning ground in a frost rim); Butcher's Wheel in steel arcs with a
  blood wake; Rotwood `zone_rot` (rotten thorns in a blight stain); the Tempest and every storm bolt
  electric blue (no white balls); a survivor's falling blow is marked by a faint gathering light,
  never a ring.
- **Frost ribbons** (`ribbon.gdshader` style 5): glints are soft points (lit cells were pale squares).
- **Sound per skill** (`Audio/Sfx.Skills.cs`, routed in `SoundBridge`): a voice per art on cast, on
  landing and on hit; strikes, chains and beams now sound. *Not heard: checked as spectrograms of
  the game's own mix only (`--wav PATH` records it; `vfx/spec.py` draws it).*
- Seen after the fixes: Gyrestorm's wind thinned; the shield's break a shockwave, not a ring;
  Thunderclap's burst blue. Eight skills taped: no clipping after the palm and pot were lowered.
- *Not yet seen*: Moonfall's arcane burst skipped (it was pink-white balls under each moon);
  Frostfire's frost ribbon removed (it drew pale squares even with round glints); the won night's
  softer shaft foot and the way out's band (`won5` was shot, not looked at).

## Next, in order

1. Shoot and look: Moonfall, Frostfire Comet, `won5` (the way out late in the won night).
2. The evolutions still wrong (all swept; sheets in `vfx/v1/`, triage sheets `vfx/v1a..d.png`,
   rechecks `vfx/u3a.png`, `u3b.png`):
   - hoops: Rend and Mend and The Harrowing (their opened sweeps still read as wide bright arcs:
     thinner and darker, or a scythe seen to travel), Winter Ward and Absolute Zero (`nova_frost`
     fronts), the Wild Hunt's green rings;
   - white bars: Skybreak (`arc_sky`, a wide white column), Ford Ice (`spear_ice`, a white bar),
     Sunlance (`beam_sun`, a thick cream beam);
   - Dawn's Judgement's discs read as soft gold blobs; Barrow Host's knights as pale ghosts.
3. The arts (Ev.Ability), then the arts' and the grounds' sound.
4. The judgements on the status page (the struck flare's white; a listen to the sounds).

## Decisions (why)

- **No hoops**: a ring on the ground with a bright edge reads as interface or geometry. A band of
  light is soft both sides, and only where a place must be marked (the way out). A fire's reach is
  its own light: a flat disc of firelight out to 5 m read as an orange circle painted on the ground.
- **Light upright on the screen, gaussians never an edge, held below the knee** (inherited).
- **A union is its own thing**: never another skill's art borrowed whole.
- **The view is told what a thing is** (`LastDot`, `HeldUntil`): never guess a tick from a blow.
- **Measure**: warm-glow widths by R−B along a row (`vfx/warmth.py`); sound by spectrogram.

## Failures, and why

- **Shader branch order**: kinds 8 and 9 fell into kind 7's `kind > 6.5` branch and drew as blue
  shafts. Bound each branch both ways.
- **The fire's room** (kind 9) read as a painted orange disc; removed.
- **The deadfall as an ellipse** of cards was a hoop of flame round a cold log; pressed to a line.
- **Two breath puffs** a pant were lost from 30 m up; three bigger, paler ones read.
- **Big sheets cost context**: a 4×8 sheet is ~5k tokens. Use `vfx/pick.py` (one frame a run,
  `max` picks the frame furthest from the run's mean) and `crops.py` at full resolution.

## Gotchas

- **Setting up a worktree** (as before): junction `godot/assets` → `public/assets` and
  `git update-index --assume-unchanged godot/assets`; robocopy `.godot` from a recent skills
  worktree (2 GB); copy `public/assets/**/*.import`; build and import twice (`vfx/imp.sh`).
  `vfx/repoint3.py` is the model for pointing the tools at a new worktree.
- **The worktree guard** refuses `cd X && git ...` chains and Python heredocs that write files.
  Write `.py` files with the Write tool and run them; `vfx/ed.py` does exact replacements and keeps
  each file's line endings (most files are CRLF in the worktree).
- **Shots**: `--on boss` adds frames at each boss move (`NAME_<label>_N`), `--won` the fall
  (`NAME_fall_N`); `--wav PATH` tapes the mix (works with `--shot`).
- Godot picks up an edited `.gdshader` at its next launch, without an import.

## Collaborators

- **Main session**: merges; rules on judgements.
- **Combat** (`a427a874da78cba8b`): the fed deadfall, "His age"; Rotwood's and Frostfire's art keys.
- **UI design** (`aa1f430bd64b8d1ce`): the way out's band sits under their prompt.
- **Animation** (`aa15f092820132274`): `CrowdView` (the flare caps, `LastDot`, `HeldUntil` are in it).
- **Arena art** (`aba487928a1515c93`): the deadfalls; BattleFx draws the fed flame over their fires.
- **Performance** (`a0eb8c612c94d4aa5`): costs on the status page.

## Files to read first

1. `docs/team/skills.md`
2. `godot/src/Fx/BattleFx.Story.cs`, `BattleFx.Loot.cs`, `shaders/loot_beam.gdshader`
3. `godot/src/Fx/BattleFx.Skills.cs` (flights, hits, `PotBurst`, `FrostfireBurst`, grounds)
4. `godot/src/Audio/Sfx.Skills.cs`, `SoundBridge.cs`
5. `godot/src/Actors/CrowdView.cs` (flare caps)
