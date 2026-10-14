# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1`, worktree `.claude/worktrees/agent-af0782e2e3f51bc1f`.
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

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
