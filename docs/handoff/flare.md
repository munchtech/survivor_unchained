# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1` (merged; the worktree is removed after the merge).
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

## Done (successor 10, 19 October): Burns Twice merged; the area is closed until the next Flare build
- **Judged:** judge 6 (`survivorsunchained_inputs/flare10/verdict_j6.txt`, on s18): NOT READY, 4/18 frames shipped;
  keep the BOOM, 2 fixes, 4 cuts. Fix solvers A (02fda81e), B (38a9f18b), C (3238a756). Judge 7 (`verdict_j7.txt`, on
  s19b, gate-only): MERGE after two fixes (beige "mannequin" corpses, the flat orange tail), verified by numbers on s20:
  beige 0.46/0.02/0.01% at night f85/f100/f113 (limit 2%; by day the bodies are black, the box measures sunlit dirt),
  orange tail 0 px after erosion night f100 and day sd100 (limit 50). Light s20: night peak 1.71x, 1 frame over 1.5x,
  knee 1.74%, swings 1.5/s; day 1.04x. Empty field: 11 frames over 1.5x at mean 0.16 absolute, knee 2.89% (accepted
  as a logged exception by judge 6 C(i): peak mean <=0.20, knee <=3%).
- **Kept:** the BOOM (birth atlas e6 + a density x age heat map, `gm_*` in flare_fb.gdshader, FLARE_GM override), the
  ring (7 px hot edge, ~32 px orange body, soot skirt; `FL_RING_*` in flare_world.gdshaderinc), varied birth sparks
  with streaks, cyan glass shards under the fire, cracks only behind the ring (veins dark by +1.6 s), impact scorches,
  every body the ring passes charred within 3 frames (audit line in the shot log; `vat.gdshaderinc` now gives the
  fire's colour to frozen bodies only), brown thin soot (sim soot max 0.6), the frost fading by alpha behind the ring.
- **Cut:** all steam, the dust discs, the melt crust/lip/glints, the post-BOOM ember flakes. The pre-BOOM dip is a 2%
  breath (was 10%) and the press drain a tenth (was a quarter), to keep swings under 2/s.
- **Gameplay-visible:** after Burns Twice the drops show at the Return's end (+4.2 s, rippling out over 0.6 s;
  `FlareFx.DropsShow`), so 250 embers don't read as confetti on the char. Revert there if the owner wants loot at once.
- **Stand-ins (all seven other Flares):** shared dip and sparks; a crescent on the Bill and Drag, a blue glow on the
  Branding (sheet `survivorsunchained_inputs/flare9/other_flares_state.jpg`).
- **Backlog for the next Flare build:** the Road's Toll and One Arrow barely show at the play camera (fail "every press
  visible"); judge 6's money shot (statues glow orange from inside ~3 frames as the ring reaches them, then shatter);
  judge 7's after-merge notes (the ring reads as a burnt-paper edge, not a wall of fire; f76's body brownish; day
  shards lean blue paper; at night the fire fades fast f88-f96 with little smoke); the sound (the owner hasn't listened:
  captures with sound in `survivorsunchained_inputs/flare10/burns_twice_an.mp4`, `_sd.mp4`).
- **Not the Flare (routed):** the day loot-label flood and tutorial popup at +1 s (UI); she reads as a dark ball from the
  play camera at night (character/camera).
- **Keep-list:** kept `survivorsunchained_inputs/flare10/` (verdicts, strips, `frames/` = the 43 judged frames of s18,
  s19b, s20), `flare9/scripts/`, the solvers' measuring scripts in `scratch_8f465914/flare/`. Cut with the worktree:
  `godot/.shots` (36 GB) and `tools/fxsim/.shots` (14 GB of bake renders, regenerable from the tracked birth.py /
  boom_sim.py; the atlas is committed).

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique"; "sounds that feel awesome".

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
