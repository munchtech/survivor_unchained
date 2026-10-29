# Handoff: skills look and feel

## Combat VFX 4 (vfx-4, 28 Oct night): WAITING ON THE OWNER'S PATTERN PICK; then one judge and the color A|B
**The owner's notes (via main), in order:**
- "what I do miss is the hatch patterns"
- "the old hatch was stylized, a cool design. this new one is just a grid"
- "it dosn't have to use the old one, just be less boring than a pure grid"
- A reference sheet of 7 typed lane telegraphs (`survivorsunchained_inputs\vfx4_owner_ref\telegraph_ideas.webp`): "colored by the ability type could be neat"
- "the half hatch without the cross is pretty nice"
- The charge-up "cast bar" FUNCTION is a keep; its look is ours to restyle.
- Likely pick: `vfx4_owner_ref\lava_half_hatch_lean.png`, a molten half hatch.

The coordinator's ruling: THREAT goes on the rims and the front (red for elite and boss; the salmon/scarlet pick applies). TYPE goes on the pattern inside (plus the lane end caps).

**Built** (branch vfx-4, all in `godot/src/Fx/MarkPass.cs`; red marks only, the crowd's amber decals are unchanged):
- **Patterns inside a red mark, chosen per mark:**
  - 0 `grid`: tonight's crossed grid.
  - 1 `hatch`: a carved half hatch. One diagonal family, uneven weight, a wandering spine, pointed at the rims.
  - 2 `chevron`: points the way the blow runs.
  - 3 `molten`: leaning bands of molten cells, veins and hot spots, with charred, darker bands between.
  - 4 `cracks`: cracks along cell edges, frost tint.
  - 5 `lattice`: a diamond lattice with studs, gold tint.
- **How they light:**
  - Each pattern is lit behind the running front; ahead of the front it shows at `hu` (0.3). The charge reads as the pattern catching light, and the front stays the brightest bar.
  - Off over the still water (`hwat` 0), faded across the bank.
  - Strokes are never thinner than half a pixel, and detail fades out near 2 px, so nothing shimmers.
- **Data** (`godot/data/mark_look.json`):
  - `"look"`: scarlet or salmon. This is the color pick, a one-line change; env `MARK_LOOK` overrides it for shots.
  - `"patterns"`: the telegraph's own `Ev.Telegraph.Pattern` if it names one (a skill can); else its `School` (Fire molten, Frost cracks, Holy lattice); else its shape (line chevron; circle, cone and ring hatch); else the default, hatch.
  - `Battle.ScheduleStrike` now sets the School on enemy strike telegraphs.
  - Pack carries the pattern id in the roof float (roof + 2 x id).
- **The lane's far end is a spear tip** (`cap` 1; 0 brings back the old soft end).
- **Pattern tint** (`ht` 0.35): the pattern takes a share of its own color, and its light may pass the red's fold up to 1 + 4 x ht, so molten veins run orange. With `ht=0` it all stays red.
- For shots, `MARK_TUNE=hs=<id>` forces one pattern on every mark (-1 = each mark's own).
- Tests: 1275 passed, 0 failed, 10 skipped.

**Candidates sheet (sent to main for the owner):** `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_vfx4\candidates_1to1.jpg`.
- 1:1 crops of the Knight lane mid-charge, day | night.
- Rows: OLD, grid, half hatch, chevrons, molten (tint on and off), cracks, lattice.
- Smaller halves: `candidates_part1_small.jpg` and `candidates_part2_small.jpg`.
- The shot scripts are in the same folder: shoot.sh (`NAME:LOOK:KIND:MARK_TUNE`), sheet.py, and pace.py for the Prologue's Knight and the Warden over the river.

**My read (not judged):**
- Molten fits best, but at 1:1 it still reads mostly red. If it's picked, push it toward the reference: bolder veins and hot spots, a hotter tint in the lit bands, and keep the charred bands see-through.
- Half hatch and chevrons read clean.
- Cracks read well at night.
- Lattice is busy by day.

**Next (successor, after the pick):**
1. Apply the pick in `mark_look.json` "patterns", and tune that pattern if the owner asks.
2. Shoot the same frames for A (scarlet) and B (salmon):
   - day and night;
   - the packed crowd (`crowd`);
   - the Grave-Caller arena (`gc`);
   - the Prologue (pace.py): the night Knight lane and the Warden's charge over the river, which is the water case.
3. ONE xhigh judge on the pattern, round cap 2. It checks the whole-frame gate, readability in a packed fight, the water case, and that the cast bar still reads.
4. Make the owner's A|B sheet (3-4 frames at 1:1), then send MR READY to main.

Cost so far: lead about 170k, no helpers, $0 API.

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
