# Solver idle 1: her town idles for the reaver, arcanist and stalker (animation 44, item 3, round 1 of 3)

Spawn on su-lead-high, effort medium, Context budget 200k. Report in your FINAL message to animation lead 44, the lead that spawned you (never to main).

## The owner (19 Oct, OWNER_NOTES "Natural idles")
"I adore the idle sway back and forth you made the warden do in town its great. I love natural looks. a lot of the looks are rigid even when safe." Then: "non movement is ok - just not if its a weirdly rigid pose - its anxious."
- **The bar is relaxed, not busy.** Stillness is fine, but tension fails.
  - Tension reads as raised shoulders, arms locked or held off the body, a ramrod spine, weight even on both feet with a level pelvis, clenched fists, or the head held rigidly forward.
  - Relaxed reads as weight on one hip with the other knee soft, dropped shoulders, arms hanging with the elbows bent, and an easy spine and neck. A slow weight shift, a breath and an occasional settle are welcome.
- **The reference is `idle_warden_town`** (tools/anim/clips/idle.py: the 100STYLE WiggleHips take, `warden_town` arms). Match its feel, not necessarily its shape. It is the same woman in every calling, so sharing its base is fine. A different stretch of the take (`mocap.idle_loop(window=...)`) or another relaxed 100STYLE take per calling adds variety cheaply: your call, but stay as good as the warden's.

## Where and how
- Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40`, branch anim-40. godot/assets is a junction: never stash, reset --hard or checkout . there.
- Commit as you go and push. Never commit heroine.res, *_clips.json, manifest.json, arms_rest_godot.json or *.import.
- Take Blender and Godot only through tools/turn.py --wait, and give each turn back at once. Stop only PIDs you started. Never build, pack or shoot the male hero (no `--body hero`).
- Build with `python tools/anim/build.py --no-pack <names>`. Never run `build.py --help` (it does a FULL build), and never run `motion.py --help` (it runs every clip).
- For the shoot and measure commands, read `solver_atk_brief.md` "Where and how" (in this folder).
- **You build and measure.** A runner shoots: write the shot list and stop. Make no judging pictures yourself beyond one half-size working look if a number leaves you in doubt.

## How town works today (read the code, don't trust this blindly)
- `PlayerView.Calm` sheathes only a calling that has `idle_<calling>_town`.
- `Mount(sheathed)` then asks `People.Clip(person, Idle/Jog_Fwd_Loop, "town")`, and `OwnClips.For` resolves `idle_<calling>_town` and `run_<calling>_town`. With no town run it falls back to the ARMED run, hands posed for a weapon that is now sheathed.
- The sprint follows the run.
- Stops and breaks use `Sheath.Pick` and play nothing when there is no town clip.
- Sockets by kind (`logic/Play/WeaponSockets.cs`): axe on the hip_loop, wand on the hip_belt, daggers on the belt_back, crossbow on the sling. **The staff has no socket and stays in her hand** (a walking staff).
- Her kinds: reaver axe / axes (gyre_axes), arcanist staff / wand, stalker crossbow / daggers. The town idle is looked up per calling, not per kind, so the arcanist's staff and wand would share one town idle. That can't work: one holds a staff, the other has her hands free.

## The job, in order
1. **Code (small).** When sheathed, try `idle_<calling>_<kind>_town`, then `idle_<calling>_town`, and the same for `run_`. Then add `idle_arcanist_staff_town`. Keep the warden working unchanged. Add a test beside the existing OwnClips / Sheath tests if one fits.
2. **The idles:**
   - `idle_reaver_town` (axe and axes: hands clear of the hip-loop axe heads);
   - `idle_arcanist_town` (the wand sheathed, hands free);
   - `idle_arcanist_staff_town` (the staff held as a walking staff at her side, butt near the ground, hand relaxed on the shaft at about hip-to-chest height, the other arm hanging; the staff butt slides no more than about 2 cm over the loop: pin that hand in her root frame rather than the chest's if you need to);
   - `idle_stalker_town` (crossbow on the sling, daggers at the belt back; hands clear of both).
   - Each one: weight on one hip, soft knee, shoulders down, elbows bent 10-25 deg, fingers relaxed (not fists), head and neck easy and level. Loop seam clean, feet locked.
3. **Town runs, only if needed.** For each calling, decide whether the armed-run fallback with sheathed pieces is wrong (a fist or hand posed around nothing, the arm abducted for an absent axe). If it is, add `run_<calling>[_<kind>]_town` from `run_warden_town`'s spec (hands relaxed, its judged swing) without `hilt_carry`, arms clear of that calling's sheathed pieces. The sprint follows (`sprint_stop.py`). The staff keeps her armed staff run (it's in her hand anyway).

## Measure (numbers before pictures), against idle_warden_town on the same scripts
- Pelvis lateral sway (cm, peak to peak) and its period; pelvis roll (deg); the share of the loop with her weight clearly on one foot.
- Shoulder height above rest (cm, both); elbow bend; how far the fist closes (fingers relaxed?); head pitch and roll range.
- Arm into body, and hand or arm into each sheathed piece (mm; `motion.py <names> --outfits`, `armscheck.py --sockets`, or `tools/scratch/anim37/sweep.py`'s sheathed-piece check, whichever applies); foot slide; loop seam jump.
- audit.py: no flags. Staff: butt drift over the loop (cm); fistfit staff stays as it was.

## Shot list (the runner shoots it; write it to `tools/scratch/anim40/shots_idle1.txt`, format as shots_atk5.txt, zone and time day)
Facing 315 unless said. Hold the town clip by name (the hold sheathes a `*_town` clip).
- Per idle (reaver with axe, reaver with gyre_axes, arcanist wand, arcanist staff, stalker crossbow, stalker daggers): `_c` (close-up, closest zoom) at 0.0, and `_p` (play camera) at 0.0. Four `_m` (0.6) frames across the loop at 0, 25, 50 and 75 % of its length, so the judge sees the sway.
- The reference: idle_warden_town `_m` at 0/25/50/75 % and `_c` at 0.0.
- Each new town run: `_m` at 0.0 and 0.175, and `_p` at 0.0.

## Return (under 30 lines)
For each clip: built / not built, the measures next to warden_town's, contacts. Then the code change and its test, the commits, the shot list path, and what's open.
