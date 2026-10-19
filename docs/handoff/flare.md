# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1`, worktree `.claude/worktrees/agent-af0782e2e3f51bc1f`.
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

## Paused here (successor 9, 18 October, coordinator wind-down); next:
- Integration 19c4915e merged (5d23b6f8). No judge has run yet, so nothing is cut and nothing judged. No turn held.
- **The BOOM now lands at f67 of the lq 60 fps run, not f114** (the whole beat shifted 47 frames after the merge; the
  press-to-BOOM is unchanged as far as the frames show). Every old frame number shifts by -47: +1 s = f127, +3 s = f247.
- (1) Light: DONE by the numbers. I(t) re-shaped (0.5 under the flash, 1 by ~f70, slower decay), undip 0.6x, and two
  defaults from a sweep: `FireGain` 0.8 (the fire after the flash, `FLARE_FIREGAIN`) and `FireRim` 0.7. Arena night
  (sweep A): peak 1.68x, 1 frame over 1.5x, sustain f69-f93 1.31-1.44x; day 0.85-0.90x. **Open:** the empty field is
  still 23 frames over 1.5x (peak 1.86x; FLARE_LOOK 1.6 allows 4); gain 0.65/rim 0.6 gave 11 and an arena sustain
  1.28-1.36x. The fire itself is the excess there, not the world light (rim-off A/B). Decide at the judge: accept for
  the empty press, or make the gain follow the crowd.
- (4) Judge 4's 4-9: built by a medium solver (commits 9e268781..87b92af2; shot s9c = `Ls9c_an_*`/`Ls9c_sd_*` in
  `.shots`, BOOM f67; taken BEFORE the light defaults). Its own misses: ring hot band ~16 px (target 20-30), outer hue
  23-25 (25-35); shard cyan coverage far under target; a white crust on the frost's outer edge at +1 s (cause unknown);
  **steam doesn't show (cut it if the judge doesn't see it)**; scars not re-checked. Glow particle cap 2600 -> 3400.
- **Next:** one shoot with the light defaults (`KEEPALL=1 bash $S/lq.sh s18 an sd`, $S = 34daaf5d `scratchpad/s`;
  run `Godot --headless --import` first if turn.py says STALE), then ONE combined max judge (whole-frame gate first) on
  the BOOM + 4-9 at 1:1 full frames: night f66 f67 f69 f72 f76 f80 f85 f93 f100 f113 f127 f187 f247, day f67 f76 f85
  f100 f127, the scars beat row `s18_an_b9_last_1.png`, plus a small f60-f130 strip for motion. Main's rule: an item
  that's a NO in round 1 is CUT, not re-roled. Then (3) the atlas only if the birth fails, (6) captures, (7) tests + MR.
- (5) Other Flares: DONE, one shoot (sheet `survivorsunchained_inputs/flare9/other_flares_state.jpg`): all seven are
  stand-ins (shared dip and sparks; a crescent on the Bill and Drag, a blue glow on the Branding). **The Road's Toll and
  One Arrow barely show at the play camera: they fail "every press visible".** Backlog for the next Flare build, no fixes.
- Scripts: `survivorsunchained_inputs/flare9/scripts/` (`rr.py TAG [-r a,b,step]` = luma ratio per frame and frames
  over 1.5x; `gsweep.sh` = 100-frame runs with env knobs). This session's Temp scratchpad was wiped mid-run; keep
  scripts there. Keep-list: not started (`.shots` holds only s9c + old kept frames now; C: 64 GB).

## Paused here (successor 8, 18 October: queued until cinematics frees its slot); next:
- Integration merged clean at 8834b4dd (no conflicts; `godot/assets` junction still points inside this worktree).
  Nothing tuned, shot or judged yet. No turn held. The main checkout's stray `FlareFx.cs`/`FlareFx.Burns.cs` are 0 bytes (nothing to save).
- Old scratch dirs (59a43b82 `flare/`, 1be2d2a9 `f6/`, 34daaf5d `s/`) still exist, so `fin16.sh`/`lq.sh` run as written; write new sheets to `flare_boom17/`.
- Fixed list (the owner, 18 Oct: finish and merge): (1) tune s16's light ("Next" 1; knobs: `flare_fire` I(t) at FlareFx.Boom.cs:150, `undip` :164, FLARE_FIRELIGHT);
  (2) judge 5c on the BOOM, whole-frame gate, max; (3) atlas solver (b5e) if the birth fails; (4) judge 4's 4-9 under the 2-3 round cap, cut what can't pass;
  (5) other Flares' state, one shoot-and-look for unseen ones; (6) owner captures (`f5/cap.sh`) to main first; (7) `dotnet test`, MR READY, keep-list for `.shots` (33 GB) and `tools/fxsim` (14 GB).
- C: had 63 GB free at the pause; check before each render (stop under 50 GB).

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique"; "sounds that feel awesome".

## Paused here (successor 7, 14 October: the owner paused the Flare area until the heroine's beautification is done); next:
- **Branch flare-1 @ c333d269, NOT merged, nothing merge-ready** (unjudged since judge 5b; integration 11faa105 and
  later merged in). No solver running, no turn held. Inputs: `survivorsunchained_inputs/scratch_34daaf5d/`
  (`flare_boomNN/` sheets; verdicts `flare_boom10/verdict_j5a.txt`, `flare_boom15/verdict_j5b.txt`; `scripts/`, `sv/`).
- **Judge 5b (on s15): NOT READY, a real step up.** The f114-f117 flash (white-yellow heart, core 15-20% of the ball)
  now beats the freeze for ~4 frames; bubble wrap gone; the fire lives to ~f160 with no hard cut; ring no longer cuts
  the ball; loot labels hidden; day floor 0.78x. Fails: the world never reacted (statues teal), the life a flat orange
  splat with the ground showing through, the sustain f120-f132 (1.13-1.21x) below the freeze's 1.31x hold.
- **Against judge 4's list:** 1 birth WEAK (5b: folds are ink lines, not valleys; tongues stubby; heat dies by f120);
  2 fireball light: rebuilt after 5b, unjudged; 3 soot: lit, eroding, unjudged after 5b's fixes; 4 shards, 5 cracks,
  6 melt/steam, 7-9 ring mass/birth/scars: not started (shards now under opaque soot and fire; 5b wants silhouettes).
- **Built (all on flare-1):** atlas **e6** = `birth.py` preset **b5e** regrading every frame of bake b5 (no handover;
  masses, folds, heart falloff, 5 tongues, a life that chars inward into lit soot), take `burns_boom5e`, render
  `sv/full.sh NAME` (~25 min) then `pack.py atlas .shots/NAME godot/art/fx/flare/burns_boom.png --cols 7 --force`.
  Game side (`flare_fb.gdshader`, `FlareFx.Boom.cs` BoomTick): heart pushed past AgX white (`hot`), body pre-saturated;
  the birth exempt from the dip to f124 (`through`), after it only the hottest fire (`undip`); fire opaque where bright;
  veil clip let go f120-f134; rise 4.5 m ease-out from f120; soot lit by its own value (`soot_lit`, `soot_up`), 0.85
  to f142, eroding (`erode`), gone by f174; day dip 25% (FlareFx.cs). The world lit by the ball (global `flare_fire`,
  I(t) 1 to f118, 0 by f155): statues' faces mixed to its colour by N.L (`vat.gdshaderinc`, `flare_fire_w`), a warm
  ground pool within 5 m (`flare_world` end of `flare_ground`); #FFB060 light 3 m up (`FLARE_FIRELIGHT`, 9; 4 changed
  the peak by 0.03x only). `FlareFx.LabelsAlpha` hides ground labels and the tip line ("THE MAP") to fire-out.
- **s16 (after 5b's fixes, UNJUDGED, sheets `flare_boom16/`):** arena peak 1.81x @116, 4 frames over 1.5x (the rule's
  limit), knee 0.6-0.8%, swings 2.5/s (f134 +10% the hot band, f147 -10%); empty 2.05x, 10 frames over (cap 4); day
  1.04x, floor 0.78x, no milky veil in the numbers. The extra light is the world lit at f116 (I(t)=1).

## Next, in order (judge 5b's fixes; full numbers in verdict_j5b.txt)
1. Tune s16's light: I(t) and the ground pool lower at f114-f118 (peak back to <=1.7x arena, <=4 frames over in
   empty), `undip_lo`/`undip` so the hot band doesn't re-brighten the frame at f134 (swings <=2/s); 5b wants the
   sustain f120-f140 at 1.30-1.45x arena from the world's warmth, not the flash.
2. Judge 5c on the BOOM (one face; sheets via `scratchpad/s/finNN.sh`, plus 5b's wanted numbers: statue rim luma/hue
   at 3/6/12 m f117 light on vs off; fire p10/50/90 at f126/f132/f140; ball share every frame f116-f134).
3. Atlas (a max taste solver, preset b5e in birth.py): folds as valleys 12-24 px, 4-8 medium billows per mass, tongues
   30-45 px held f115-f120, core >=10% of the ball at f118, hot band >=25% f118-f122, charring ~5 frames later
   (fire share >=85% to f130), day body hue 25-32.
4. Then judge 4's 4-9 (shards as glass/silhouettes, cracks, melt/steam, ring mass and birth, ember scars), then
   captures for the owner (`f5/cap.sh`).

## Tools
Old scratch (still on disk): `59a43b82.../scratchpad/flare/` (`lq.sh TAG`, `batch8.sh TAG`, `jsheet.sh TAG`, `sheet.py`,
`lum60.py`, `meas.py TAG`, `shot.sh`). Lead 7 (`34daaf5d.../scratchpad/s/`, backed up in `scratch_34daaf5d/scripts/`): `finNN.sh` = lq.sh an+sd+empty, ball.py, bands.py, swl.py (counted swings), judge sheets incl. `crop100.py` 100% crops. Lead 6 (`1be2d2a9.../scratchpad/f6/`, backed up in survivorsunchained_inputs/scratch_1be2d2a9/flare/f6/): `lq.sh TAG an sn sd` = clean rows (to +6 s) + 60 fps runs + `lum.py` (peak, knee, swings, Return floor; EXTRA="--horde 0" for an empty field); `reach.py` in-reach vs outside; `js.sh TAG LATE` judge sheets; `grid.py`, `crop.py`, `ed.py`. Lead 5: `1be2d2a9.../scratchpad/f5/` (`q.sh TAG an` = import + clean row + a BOOM
sequence at 20 fps from 7.75 s; `lqs.sh TAG` = Verge night lq; `cap.sh`; `onset.py WAV t0 t1`; `bisect.sh`).
Backed up in `survivorsunchained_inputs/scratch_1be2d2a9/flare/` (with `f6_boom.jpg`).
Build C#: `dotnet build godot/SurvivorUnchained.csproj -v q`. Tests: `dotnet test godot/tests/Tests.csproj` (887 green).

## Gotchas
- **turn.py take needs `--root <worktree>`** when called from scratch (the freshness gate checks the cwd's checkout);
  `scratchpad/s/lq.sh` and `tools/fxsim/rr.sh`/`run.sh` pass it. After any merge or art change run Godot `--import` first.
- 14 Oct: a merge attempt replaced the `godot/assets` junction with git's text-file symlink and `public/assets` was
  missing (858 files). Restored with `git checkout -- public/assets` and a junction to the worktree's own
  `public/assets`. Check `ls -la godot | grep assets` points inside this worktree before shots.
- A `# comment` added mid-line in a birth.py preset swallows the keys after it (KeyError life_noise, 14 Oct).
- **NEVER `git stash`, `git reset --hard` or `git checkout .` here** (godot/assets junction; see README DANGER).
- NEVER `python -` (it hangs, even with a heredoc). Write a .py file.
- Mantaflow: setting any domain property after `cache_directory` deletes the bake (it is set last now).
- pack.py once handed PIL float64 planes as "F" and wrote noise into every resized cell: keep the float32 cast.
- The Flare clock runs at 0.1 during hitstop; the column/particles and the sim quad run on real time.
- Solvers run out at about 200-220k after one round. Give them one problem and a working pipeline.
