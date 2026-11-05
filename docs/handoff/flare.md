# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4. Branch `flare-1` (merged; the worktree is removed after the merge).
Numbers are classes' (paused; send anything for classes through the coordinator). Her clip is animation's.

## H7 Flare: an ultimate (flare-h7, 4-5 Nov): MR READY flare-h7 (code at bebbf38ed, the suite green there; this handoff commit on top). Judge r3 (last): Long Cut PASS WITH KNOWN (close), Bell FAIL (close); knowns K1-K10 below
Brief `docs/team/hook/H7_flare_ultimate.md`; owner's line N29/N37. Scope: the 8 staged Strikes; Stands out (coordinator approved). Lead 1 (to 0fa3ce734), lead 2 (rounds 2-3, this top). Integration merged at ceb583645 (S1 story in; no godot code conflicts). Full suite on bebbf38ed: 1565/0/10. `--import` clean. Clips, frames and verdicts: `survivorsunchained_inputs\flare_h7\` (`f3d_longcut`, `f3c_bell` = final; `f3s_*` = the other six; `judge_r1|r2|r3\` = briefs, frames, `verdict.md`).
- **P7 ledger:** the app can now play every Flare as one ultimate from data (`godot/data/content/flare_family.json`: stop, grade, dust, marks, peak, ripple, band, beat, recovery, per-Flare blow/peak/fuse/tableau), with a predictor that marks exactly what it will hit (0 late across 8 Strikes), a true world hold, and a measured blow (peak, knee, kick, held px, loudness, GPU by tool). This asset cost lead 1 ~260k + 1.49M helpers + 1,308 ElevenLabs credits; lead 2 ~180k + ~1.07M helpers (solvers A 204k, B1 204k, B2 162k, C1 207k, C2 154k; runners ~135k) + $3.77 API (judges r2 $1.79, r3 $1.98). The next Flare costs about 150-250k: its family entry is data; its own art layers, one tuning pass against flare_measure, one API judge.
- **The app can now (round 2-3, on top of lead 1's marks, hold, sound and tools; see git log 0fa3ce734..HEAD):**
  - the blow beat: a 3-4 frame peak lit from the blow (`FlareFx.Peak.cs`; LC 1.41x, Bell 1.42x pre-press, knee 0.9/1.6%), a 2-frame hitstop that keeps the Flare's clock, the push-in released on the blow, a 9 px kick on its own channel (`JoltPx`), deaths/counter/numbers on the band, gold edge-only band rims (`BandRim`, CrowdView), `BandReaches/BandReachesRt/BlowAtRt`;
  - the band as a lit front with a thin gold-white edge and trough (every Flare); the Long Cut's crack TEARS with the band (`"from": "tear"`), its line's total at the far end (clamped on screen); the Bell's tableau (toll kills held standing until the third toll's band; FLARE_LOOK §1.6 names the exception), a 2.5x column with a crown behind her, an 8 m shock ring launching the band;
  - the stop: the web OUT of every Flare (FLARE_LOOK §1.2 updated), hanging dust (`FlareFx.Dust.cs`), the grade 30% deeper incl. her own lingering skill light (`BattleFx.FlareDim.cs`; danger marks stay full), her pool x1.5; marks as light pools (~115 px, tightening to ~75 px until the band reaches each foe); the LC foreshadow crack; held 0.40 px frame to frame;
  - shoot/measure: `--clip --flare` pushes her next level out of the window (`--clip-level` keeps it); `flare_measure.py` (c3) peak per frame and (c4) full-res kick; the press log prints foes in reach. Standard r2/r3 shoot (67-70 in reach): `flare_clip.py <name> --flare <id> --quick warden --cast 5 --godot-args "--flare-hover elite --horde 60 --dist 11 --spread 6"`.
- **Judge r3 (max, API):** LC "whole frame YES, narrowly": the indigo hold, the ring sweeping the screen with the white-hot tear in step, the glowing seam after. Bell NO: the blow is built (column, her over it, ring, band) but the toll rim came out a cold chrome sheen and the arms vanish at the peak. KNOWNS (closed at the round cap; distance, then what it takes):
  - K1 Bell toll rim cold chrome and stays on (close): draw it after the grade, warm gold, edge-only 2-3 px, pulse 6-8 f then hold 25%; drop the cold specular. With K2 = Bell PASS WITH KNOWN.
  - K2 deaths read as a vanish (Bell) or a fade (LC) (close): pool out on the death frame, counter on the death event, an 8-10 f ember burn-away with ash, LC lift 20-40 px, Bell push outward.
  - K3 the hold leaks (close): bodies killed just before the press ragdoll mid-stop; put death anims/ragdolls on the hold's timescale.
  - K4 numbers (close): Bell 10 of 44 shown, none on the west arm (spread the cap by area, a 1.8x total at the crown); LC total late and crit-sized (1.6-2x, on the tip's arrival).
  - K5 LC tear hidden under the crowd at the peak (close): draw the crack's light above the bodies, light straddlers from below.
  - K6 Bell tolls 1-2 show no ripple; the third toll +4.0 dB (close): a thin dust ring to 8 m in 0.2 s; the boom is held by the master limiter/duck (the bank gain is at its cap 4): audio's call.
  - K7 the Main in a dense stop (medium): max-blend pools, dim others 20-30%, the Main a white-gold core + thin ring + body rim; replace the Bell's pickup-like orb.
  - K8 stop dressing (close): fewer, larger soft motes lit by her ember; exempt her pool from the grade (it reads mauve).
  - K9 LC future crack a red scratch (close): a faint gold seam from her feet from stop+0.25 s.
  - K10 loot (close): no loot shows on either band (count stays 25: check `DropFresh` on the band); the Bell's flakes settle from the dead, not scatter.
- **Other numbers, known (not judged):** the other six run clean with 0 late marks (f3s_*): Burns 3.36x/25 frames over 1.5x/knee 3.36%, Toll 2.07x/18 f, One Arrow 1.83x/17 f are over the §1.6 light budget from their own older layers (Branding 1.22x, Drag 1.16x, Bill 1.02x within); One Arrow's kick 30.6 px (its own shake) and its mark measures 0 px (a measure gap on a line mark). GPU (measured beside other Godot runs): LC band window +1.08 ms (lead 1: +0.7 from its older cleave layers; the tear adds ~0.4; one shadowed omni at the heart, `FlareFx.Peak.cs:50`: try it unshadowed), Bell +0.38, stops +0.3. Blow minus fight +4-5 dB on the Warden Flares (the brief's 6 dB is a ceiling).
- **Routing notes for the coordinator:** (1) COMBAT (P6): the striped telegraph lane (the red-chevron band crossing the frame after a Flare, `f_longcut` +2.2-3.0 s) breaks LOOK_BIBLE row 8 (danger reads as light on the ground hugging the shape, never a printed stripe); it is combat's telegraph kit, not the Flare's. (2) UI: a Flare that kills a pack levels her at the press, and the "EMBER n" title then sits over the screen's center through the ultimate (reproduced; the clips hide it with `--clip`). (3) L1: the FX band rules (look-l1@2a28ea925, `fx_language.json`) are read but not adopted: the Flares take the bands and colors when L1's cel include passes its proof; the judge's knowns K1/K5/K8 are the natural place.
- **Next (a successor or the next Flare pass):** K1+K2 first (the Bell to PASS WITH KNOWN, the LC's main known), then K3-K6, then K7-K10; the other six's light budget with their own art.

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
