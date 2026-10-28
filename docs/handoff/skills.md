# Handoff: skills look and feel

## Paused here (Combat VFX 2, vfx-1@4b272993, 27 Oct night); next: shoot r5 day/arena/gc, ONE max judge on the re-tint, then the MR

**Done (all on vfx-1, tests 1184/0/8):**
- Integration 4f4fe6bc merged (457a7c05). 15 colliding untracked .uid files are in coordinator scratch f22ca2bc `vfx2\uid_backup`.
- Logic: `godot/logic/Sim/TelegraphRead.cs` (Of / Champion; elite+boss blows = Danger, crowd = Amber, raise ring never danger), `tests/TelegraphReadTests.cs` (table + the Ford-Warden's cleave/charge are Boss and Danger) (61cf6e41).
- Round 2 max judge FAILED (bed brighter than ground = red rug; river rose; raise ring flood). Round 3 (9e0fcfe7, a16367b1) max judge: raise ring, crowd, F7 teach PASS-WITH-NOTES; struck flash PASS-WITH-NOTES unconfirmed (her lightning crit in both sets); red line night ships with notes; DAY (cellophane box) and WATER (opaque red plank) CAN'T SHIP. Ruling: the bed must RE-TINT the ground's own light, one function over land and water.
- The approach change: `godot/src/Fx/MarkPass.cs` (ea12dea8, 8006813b, a4cfbda5, ea425c9d): a compute pass after the transparent pass (after the water; water.gdshader reads the screen and writes no depth, so no plane could see it). Per pixel: world point from depth, swapped to the water surface under the water line (`Water.Level` from `ZoneView.WaterLevel`); only near the mark's own ground (32x32 height grid) and up-facing; runs the frame's own display chain (Godot 4.5.1 AgX verbatim, sRGB, adjustments, the zone's 3D grade) so the bed = the scarlet whose SEEN value is k 0.82 x the ground's; rims and fill eased to just before scarlet folds to salmon. Lane ends fade; no slam crack on water. Env: `MARK_TUNE=k=..`, `MARK_PASS=0` (old look), `MARK_TIME=1` (GPU ms: 0.041 median). Max 32 marks, then the old decal.
- Measured r5: rims hue 0-1 sat 0.83-0.92 night, 0.88-1.00 day; bed/ground night 0.76-0.86 (outliers 1.07/1.21), water 0.75-1.08 / 0.82-0.96, day 0.65-0.81 (pre-final k 0.775), arena 0.61-0.69 pre-fix (arena rims now 2x brighter: check it didn't regress; r3 judge loved the arena). Bank dry/wet mostly within 10%.
- 237a079b: shots log the camera the saved frame was drawn with (a red mark's first frames had measured as bare ground). `TELE_F` env sets mark shot fractions; hits shot at +0/+2/+4/+8 drawn frames, normal (n) and crit (c).
- 4b272993: crowd amber #ffbc30 / bed #2a1d08 (toward hue 33); raise ring shares that amber, rim core 0.6x, breath +-15% at 0.5 Hz (the fill doesn't breathe). Not yet seen on screen.

**Next:**
1. Shoot r5 day, arena and gc (crowd mark, raise ring at full fill, a hit with blood) with the final build. **The runner's r5day/r5arena runs made NO frames** (exit 0; logs end `draft rehearsal ran fade=1.00` then `RenderingServer::get_singleton() is null`): its args were guessed. The r3 runs that worked (vfx2\logs\r3fday.log, r3farena.log, r3fgc.log) were made by the round-3 solver, whose exact args aren't recorded; find them (Game.cs `Args.Get`, the arena/encounter start) or diagnose the early quit first. Scripts: coordinator scratch f22ca2bc `vfx2\r5\` (shoot.sh, pace.py with STOP="pace stage Victory" ~10 min, m3.py, agx.py).
2. ONE max judge (whole-frame gate, 1:1) on: r5pro_teach_red_line_1, r5pro_tele41_4/_11 (Knight), r5pro_tele441_4/_16 (Warden cleave over water), r5pro_tele442_1/_15 (charge across the bank), r5pro_hit41n_1..4 / hit41c_1..4, plus the new day/arena/gc frames. Ask it to check pink on rocks/foes inside the marks (not measured).
3. Main's ruling (approved): if day or water still fails, cut the red bed to EDGES-ONLY and MR without another loop. Then full test, "MERGE REQUEST: vfx-1@<sha>".
4. After the MR: study docs/design/SKILL_VFX_REFERENCES.md + `survivorsunchained_inputs\vfx_refs\<id>\sheet.jpg`; write what our skill VFX take from them. Then the Warden's 4 new skills' VFX needs from Classes Phase 1 (via main). Memory flare-is-a-boom-button for Flare looks.

**Known, not ours:** "3 RID leaked" at exit predates MarkPass. Routed to UI via main: F7's "line" word orange (should be scarlet); crit numbers cover the body / land over the hotbar; card ghost text (r3fpro_tele43_5). No flag to strip her lightning crit for hit shots (only --weapon / --quick).
**Cost this session:** about 1.0M tokens (2 workers ~72k, 3 max judges ~420k, 3 solvers ~590k, runner 48k), $0 API.

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
