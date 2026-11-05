# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1` (merged; the worktree is removed after the merge).
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

## H7 Flare: an ultimate (flare-h7, 4-5 Nov): HANDOFF READY. Judge r1 FAILED (Long Cut medium, Bell far); round 2 is the last
Brief `docs/team/hook/H7_flare_ultimate.md`; owner's line N29/N37. Scope: the 8 staged Strikes (Long Cut, Bell, Burns, Toll, Branding, One Arrow, Drag, Bill); Stands out (coordinator approved). Branch flare-h7 (pushed), merged integration at 47c3571e9 (H6/H8 as of then). Suite 1573 (Arrow gain fixed to the cap 4.0 after the last full run: re-run). Clips and sheets: `survivorsunchained_inputslare_h7\` (`f_*` = latest; `base_*` = before H7, motion setting off; `judge_r1\` = the judge's pulled frames lc_mid.jpg, lc_0.95.png, bell_1.07.png, spot.jpg).
- **The app can now:**
  - mark what a Flare will hit: `Battle.FlareMarks` (logic/Sim/FlareMarks.cs, read-only predictor a tick ahead, mirrors each Strike's own queries; `FlareLateMarks` safety net; decision marks for Toll/Bill/Burns re-picks). FlareMarksTests: late 0 on all 8 over 24 seeded casts, marked-unhit 0.6-8.7%, determinism on/off identical. H6 agreed (their closing WALL drops when a Flare thins it: the ring's foes are marked like any).
  - hold the world for the stop (`flare_family.json` `stop` per calling 0.27-0.40 s, world rate 0; `world_time` global replaces TIME in 19 world shaders + VAT: `shaders/world_clock.gdshaderinc`, `src/Game/MotionClock.cs`), drop the world to moon indigo (flare_drain on world materials, world lights 25%), hush numbers/sparks.
  - draw the marks (`src/Fx/Flare/FlareMarksView.cs`, `shaders/flare_mark*.gdshader*`; POSITION written in every branch), the Main for the hovered foe, the line seam.
  - land the main blow per Flare as data (`flares.<id>.blow`): boom once, the Spend light, a shock band through flare_world's ground hook (`flare_band*`), kills (DeathOf), held numbers and loot (DropFresh) on the band, a 3 px kick; recovery (grade out 0.5 s, `PlayerView.FlarePool` x1.3 2 s). `src/Fx/Flare/FlareFx.Blow.cs`.
  - sound the two beats: 14 families (tools/audio/prompts.json `flare_intake_<calling>`, `flare_boom_<id>`, `bell_toll`, `flare_mark_tick`), events in tools/audio/events.py; the intake plays its take's loudest stretch cut to the stop (`SoundBank.PlayTailFor`); beds now honor DuckBeds (Synth.cs bug fixed).
  - shoot and measure: `tools/fx/flare_clip.py` (1:1 clip with sound, 14 frames, sheets; `--clip` forces default motion/sound and keeps her alive: the owner's saved motion "off" had silently removed the stop from every early clip), `flare_measure.py` (held, budget, loudness), `flare_gpu.py --run`, `--flare-hover elite` (falls back to the toughest), `--flare-band-off`, `--world-clock-live`.
- **Numbers (f_*):** Long Cut 1.83x/3 frames (a level-up)/0.23% knee; Bell 1.60x/3/0.76%; day 1.09x/0. Held in the stop 0.37-0.79 px frame to frame (under pre-press). GPU: stop +0.03-0.19 ms, band ~0.1 ms (the Long Cut's blow window +0.7 ms is its older cleave layers). Blow minus fight short-term +0.8 to +3.5 dB (master compressor/limiter cap it; the brief's 6 dB is a ceiling), intake +8 to +12 dB over the ducked world (Bill +1.1). Toll/Drag/Burns over the light budget from their own older layers (spot checks, not H7's).
- **Judge r1 (max, a5d84d8d): FAIL both Warden Flares. Keep the four-beat structure; the blow beat was never built, and the web is the wrong idea.** Fixes, ranked, for round 2 (the LAST: close as known after):
  1. A PEAK at the main blow (LC cleave +0.78-0.80, Bell blast +1.03): 3-4 frames at ~1.4x mean and 2-3% over the knee (the budget allows it; we sit at 0.2-0.8%), lit from the blow in dawn gold (LC: the whole seam erupts from below; Bell: the column + an 8 m ground disk); a 2-frame hitstop; release the push-in there; kick 8-10 px.
  2. The band as a lit FRONT: a soft 20-40 px leading edge in the school's Glow at ~2x the ground's value, the ground lit behind it ~0.15 s, from the blow frame to the edges in 0.25-0.3 s. Each Bell toll a visible air/dust ripple, no flash.
  3. No gap between mark and hit: marks stay through the blow and tighten (~110 to 70 px, brighter) instead of swelling and fading; each struck body a 2-frame rim as the band crosses it, then its number. The HUD kill counter waits for the band.
  4. REMOVE the web (FLARE_LOOK §1.2's Draw web) from every Flare: frozen dust/motes and a deeper grade instead.
  5. Rings to light POOLS: soft radial, no stroke, ~1.5x the footprint, uplight on the body; Main 2x size and value with an inner core (reads without its ray).
  6. The stop ~30% deeper in value, including other skills' lingering effects (rune circles); her ember pool up (~x1.5) during the stop; danger marks stay full.
  7. LC in the stop: the future crack lit faintly from below with a spark running along it (not a hard laser hairline).
  8. Re-shoot with 30+ live foes in reach at the press (f_longcut had 6 on screen).
  Also (i) the spot checks: hard geometry (Toll's white laser lines and star glints, Bill's red ring with blue-white bars). Telegraphs' striped lane breaks bible row 8: not H7, route it to combat.
- **Next:** one medium solver on fixes 1-3 + 8 (the blow beat as a build), one on 4-7 (stop and marks look); runner re-shoot f2_*; judge r2 (`Item: flare-h7-gate`, round 2 of the cap). Merge integration (H6, then H8 per the coordinator) before MR READY; full suite; push; `MR READY flare-h7@<sha>` here and to main AND the new coordinator `local_4f5ceed0-79a5-47f5-81d6-a1ce170715d3`, with the clip paths, the verdict in two lines, credits and cost.
- **Cost so far:** lead ~260k; helpers ~1.49M (marks sim 186k, clip worker 170k, stop/marks 212k, rings fix 59k, blow 205k, runner 71k, fixes 212k + 206k, judge 169k). ElevenLabs 1,308 credits. API $0.

## Combat VFX 12 (vfx-12, 3 Nov): MR READY. The closeout's five bugs and syncs (CLOSEOUT.md wave 1)
One high judge (whole frame first, 1:1 play camera), 3 rounds on One Arrow, 2 on the drops, 1 on the rest. Branch vfx-12; tests 1455/0/10.
- **The app can now:**
  - light the Flare's staff on the staff. The holder was "arm:mage_staff", which Godot rewrites to "arm_mage_staff", so the lookup never matched. `GripSlide.ArmNode(id)` now builds the name, and the held one (under mount_) is re-looked while missing. Log: "flare staff: held arm_mage_staff under mount_hand_r" (`--weapon ember_staff`; the quick arcanist holds a wand). Same bug fixed in `sheathed:` → `GripSlide.SheathPrefix`: PersonView.Swap never saw a piece already sheathed. GripSlideTests fails on any node name in src that Godot would rewrite.
  - land Groundbreaker's and Sunder's KILLS with the view's blow. A killed body holds its last pose, then falls, bursts and throws on DieT minus the lag (`CrowdView.DeathHeld`, `KillFx` split out of Handle).
    - Heave: day falls f45 → f60 (heave f60); night f35 → f50.
    - Crack tip: 8 frames early → 0. Sunder tip: 3-4 frames early → 0.
    - Numbers and flinch were already held by VFX 11.
  - draw Sunder's line swing without the heavy crescent over the line's base (`--wg-sl-crescent`: as before). Judge: the base is clean, and the swing isn't weaker.
  - mark every Road's Toll cut and every One Arrow arrow and split at the play camera (FlareFx.Stalker.cs, new).
    - Toll: day 900 → 2,300-6,000 px, 71 frames. Arrow: day 984 → 13,448 px, 24 frames. Burns Twice is ~55,000 px.
    - Threads follow the slope of the ground (r2's ladder was flat threads on a hillside). The glow is on every thread at half (r3: beads at night; applied after the judge, not re-shot).
  - show Burns Twice's drops as the ring passes them, the last at +0.77 s (was +4.2 to +4.8 s). They scale in over 0.3 s, then fade from 0.3 to 0.1 light until the Return ends (`Flare.DropFresh` in BattleFx.Pickups).
- **Known (closed, judge):**
  - Inside-ring drops are hard to read as loot at night: the loot or UI pass.
  - Item drops are sim pickups and still drop on the sim tick, ~15 frames before the heave.
  - Kill sounds tied to the kill event weren't checked.
  - All 12 Toll cuts stack on one target, by design. The stand-in lines are plain white: the next Flare build.
  - The night Sunder base near her is dim: pass 4.
- **Perf:** a Release ABAB (f9372bbd9 vs vfx-12, night arena, 250 horde, all four Warden skills; `survivorsunchained_inputs\vfx12\perf\`). Inconclusive: the machine was at 94-100% CPU, and A1 vs A2 differ by 2.1 ms. The changes are view-only and small: the Toll ~600 bits a press, the Arrow ~230 bits, against a 3,400 pool.
- **Strips:** `survivorsunchained_inputs\vfx12\a\` (sl_base_*, gb_heave_*) and `\b\` (item4_*_r3, item5_burns_drops_r2). Verdicts were in-session (judge a7a06521).
- **Cost:** ~0.75M. Helper A 0.155M, helper B 0.26M, fixer 0.07M, judge 0.1M, runner 0.04M, lead ~0.12M.

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
