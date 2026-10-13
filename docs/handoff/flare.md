# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1`, worktree `.claude/worktrees/agent-af0782e2e3f51bc1f`.
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's (ae15fd13a044b8303).

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique"; "sounds that feel awesome".

## State (successor 4 stopped here; 887 tests green; NOTHING passed a judge, no merge request)
- **HEAD is solver 3's WIP (86ee84d9) and it is BROKEN:** after the last word the arena night frame goes flat bright
  salmon inside the reach (3.1-4.1x of ready, 142 frames over 1.5x). The Verge is fine. Sheet: `s5_final.jpg`.
- **Bisected (lq.sh, arena night):**
  - Everything up to 3bc0cdfe, plus solver 3's C#, holds §1.6: peak 1.58x, 3 frames over (s6b). So the C# side
    (FlareFx.Boom.cs: pillar, cap, haze, jets) is not the cause.
  - Solver 3's `flare_world.gdshaderinc` alone brings the salmon back (s6c).
  - Reverting only `flare_boom()` to 3bc0cdfe doesn't fix it (s6d).
  - The cause is in the other hunks of `git diff 3bc0cdfe 86ee84d9 -- godot/shaders/flare_world.gdshaderinc`.
    Checked by reading: `flare_boom_light`, `flare_boom_flash`, the char/ember block in `flare_ground`, the web line
    (damping the web didn't change it), `flare_prop`, and `flare_crack` (`flare_crack` needs the new vat; it was off in s6c).
  - Next: swap one function at a time with `bis.py "<function head>"` (it puts 3bc0cdfe's version of that function back
    in place), run `lq.sh TAG`, and look at one c2 crop. A flat value unchanged by albedo edits smells of inf/NaN
    emission or a lit surface with no `bo.z` (check `flare_boom_behind` users, and `flare_blade`: arena leaves cover
    the whole ground).
- **Judge 2 (s4, shot at fdbdd9cc; sheet `s4_judge.jpg`): NOT ready.** The fixes worked: the statues stand (CrowdView
  skipped Flare kills marked Burst), drops are held until 1 s after each statue breaks, the ring is a thin line with no
  flecks (they were arena leaves), and §1.6 holds (1.59x, 3 frames over). It FAILED 11 (the BOOM is a soft flash plus rods,
  then a bead chain of puffs) and 21; 7 and 10 are WEAK (a gummy pale-blue carpet, square glints, the ring bursting looks like
  confetti); the Return goes near-black. Its fix list, in order: BOOM pillar + cap + jets + heat ring; ring tongues, wobble,
  red edge; statues crack then burst with orange-faced shards; char dark warm brown with amber web, the dip back to 0.75x by
  +0.5 s; frost glaze 1.5-2x ground, star glints, cyan thin edges, per-body variety; LEVEL popup held. Solver 3 built all
  the BOOM items (86ee84d9). I built the frost items and the popup hold (018e0fad, 3bc0cdfe). None of it has been judged.
- **Done and unjudged since judge 2:** glaze per-region hue, rime, narrower rim, 2-4 px twinkling glints (still reads pale at
  Verge night, s4g); `FlareFx.HoldsFrame` holds the Journey's announcements (Game.Announce) and the level pillar
  (BattleFx.LevelLight) until 1.2 s after the last word.
- **Classes' events wired (052f059d):** "aim" drops an ember that lands on its blow's frame at the Blow's TX/TZ
  (`Drop`/`WhereFalls`/`DoomUnder`); "shove" gets a skid of churned frost, and a boss rocks in a ring of it (`Shove`).
- **Her clip:** not wired anywhere in the view yet. Animation's round 8 is in work: contact f20, blend_out 46/30, run from its
  f10 over a 0.3 s fade; mage_staff.glb gets an anchor_grip (the staff moves about 3 cm). Wire it when they send the packed clip.

## Next, in order
1. Find the salmon (above), then lq.sh: at most 4 frames over 1.5x.
2. Shoot `batch8.sh TAG` and `jsheet.sh TAG`, add b4/b5 and +0.1 s frames, then a fresh judge 3 (judge 2's checklist and
   measurements: Verge day §1.6, post-BOOM floor per row, glaze/ground ratio at b6, BOOM distance from her).
3. Then embers, impacts, the Return's steam (lavender cotton at night), day colour, the clip, the owner's 60 fps captures with
   sound plus the BOOM's sound alone.

## Tools (back-ups in `survivorsunchained_inputs/scratch_59a43b82/flare/`)
`quick.sh TAG an sn sd` (clean rows, takes and gives the turn), `lq.sh TAG` (arena row + 60 fps + §1.6, deletes the frames),
`batch8.sh TAG` (judge rows + real rows + --wav + 60 fps), `jsheet.sh TAG` (judge sheet), `sheet.py`, `lum60.py`, `bis.py`.
Build C#: `dotnet build godot/SurvivorUnchained.csproj -v q`. Shaders need no build.

## Gotchas
- **NEVER `git stash`, `git reset --hard` or `git checkout .` here.** The reset rewrites `godot/assets` (a symlink kept as a
  file, assume-unchanged), and on Windows removing the junction emptied the worktree's own `public/assets` (13 Oct: 858
  tracked + 811 untracked env files; restored from git + copied from main; junction re-made to THIS worktree's
  public/assets). Checking out named files (`git checkout -- <file>`) is safe.
- NEVER `python -` (it hangs). Wait on a background job by its exact output file.
- Solvers ran out at about 200k after one round each. Give them one problem and a working pipeline.
- The Flare clock runs at 0.1 during hitstop; the column/particles move in real time.
