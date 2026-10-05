# Handoff: animation

For the next animation lead. Read `docs/team/README.md` and `docs/team/RESUME.md`, then this page, then `docs/team/animation.md` (status and the per-clip sign-off log). Written by the successor of a7dd95d00c4a6a017, on branch `worktree-agent-aa15f092820132274`. The leads before: a7dd95d00c4a6a017 and a03acf30b3e9bdd70.

## 1. The owner's bar

- "AAA", "we are striving for perfection", "not polish, perfection". Remake rather than polish.
- Motion should be "weighty, characterful, readable at the game's camera".
- From the latest tests:
  - "noticing a lot of reverse weird wrist motions ... stuff that isn't flowing naturally. it seems to be attempting to correct";
  - "were looking for natural / correct movements. just want it to be skeptical".
- Treat every clip as guilty until it is shown natural. The numbers are never the verdict: look at full resolution, at the game camera and at the cinematic's camera.
- The heroine carries sex appeal, "tho not at the cost of looking bad". The tone is 18+.

## 2. The brief

- You own character animation:
  - her (`heroine.res`), the hero (`hero.res`) and the folk (`folk.res`);
  - the crowd's keyed motion (`crowd.py`) and the beasts' (`Beasts.cs`);
  - the cinematics' clips.
- Tools are in `tools/anim/`. In `godot/src/Actors/`, change animation mapping and playback only. This round also touched:
  - weapon mounts (`Arms.Hold`'s lean);
  - `GameFall.cs` (her fall and get-up).
- Take a turn for every Godot run, packs included (`tools/turn.py take godot "animation: ..." --wait N`).
- Run `dotnet test` in `godot/tests` before commits (762 pass). Commit and push your branch. Open no PRs. Use British spelling.

## 3. Done this round (pushed: c21ea122, dd21d37b and the commit that adds this page)

- **The wrist.** The single 80-degree wrist limit is gone.
  - `keyed.Rig` sets FLEX 75, EXT 65, RADIAL 22 and ULNAR 38, read on the wrist's own axes, which turn with the forearm's roll (`_wrist_split`, `_wrist_clamp`, `_wrist_over`).
  - The elbow's swivel search uses the same range.
  - Retargeted takes are held to it (`retarget.keep_wrists`).
  - 8,899 frames were past a wrist's range, as scratch `wrist.py` measures it with tight limits; 637 are now, most within a few degrees. The audit, with its wider limits, now flags none.
- **The diagonal grip.**
  - `keyed.GRIP` and `Arms.Spec.Lean`: sword 35 degrees; axe, daggers, mace and wand 30; staff and crossbow square.
  - It applies to her and the hero only: `Rig.grips`, and `person.Own != null` in `Arms.Hold`. The folk also play the library's clips, held square.
  - A clip's `meta.weapon` sets it (`grip_of`). `anim_review.gd` mounts the same lean.
  - `_whole_aims` fills blade and knuckles in the grip's frame.
- **The `thumb` control:** the wrist straight, the forearm rolled toward a direction.
  - Used for carried blades (`run.blade_carry`), the reaver's twirl and `bull_rush`'s drawn-back sword.
  - Thumb-only keys skip the swivel search.
  - Mixed with blade keys, they are filled by `_whole_aims`.
- **Re-keyed:**
  - `warden_show`: the sword raised overhand, the point down over the rim at you, the face clear;
  - the runs and sprints: the sword hand at her side and ahead; the sprint's arm capped at 85% reach;
  - `bull_rush`;
  - `chain_strike`: a frame for the axe to come down; contact moved to 3/30;
  - `cast_raise`: the staff across overhead, then upright in both fists;
  - the reaver's twirl;
  - the folk's `die_front`.
- **Ground:**
  - `death`'s knees and shield, and `get_up`'s knees, no longer sink. The shield lies face up and the blade lies flat.
  - Retargeted takes lift the hips where a knee or a seat would go into the ground, then re-reach for the planted ankles (`retarget.retarget`). This fixed leap's landing.
  - `lie_side_wake`'s elbow dip is shortened.
- **Her story fall:**
  - `StoryNight.OnFall` keeps her at 1 HP, so she used to stand through her own fall.
  - `PlayerView.Fall()` (from `GameFall.StoryFall`) now puts her down; `Revive()` (from `GetUp`) plays `get_up`.
  - The UI's build7 shot was the male hero (green); pass `--sex female` for her.
- **`flinch`:** a new gesture, a jolt of the back and head. It is laid over a run or a blow when she is moving or mid-blow; standing, the old upper-body `hit` plays.
- **`audit.py`** flags a wrist past its range (FLEX 85, EXT 75, RADIAL 30, ULNAR 45: wider than the solver because its axis is the hand's, up to 13 degrees off the forearm on the hero).
- **Audit totals:** 231 frames flagged, down from 894 when this round began. One clip spins over 90 degrees in a frame: the hero's `chain_strike`.
- **Strikes:** judged at the arena camera at 1.6 times; they read and no flip shows.
- **Strips:** sent to the main session as one batch (`anim5/sh/ba5_*.png`, plus the predecessor's `anim4/sh/ba_*.png`).

## 4. Next, in order

1. **C01 and C04 in their cinematics,** once cinematics has blocked them in. Use a local cue swap (scratch `cue.py`, never committed). The hands that were keyed past a wrist's range now fall short: look at `cup_hands`, `letter`, `reach_coals` and `sit_back_heels` close up. `flask_drink`'s spout stays on her lips (scratch `contact.py`).
2. **The Warden's `lie_arm_up` and `wade_drag` in C02.**
3. **Grimtunnel's `burst_hug`, `sniff`, `laugh` and `dive`, and the lampling's slam** (`Beasts.cs` compositions). Nothing in the game asks for these roles yet, so agree the moments with combat first (`GrimtunnelStory`: Under, the burst, the lamps).
4. **The male hero's library** with ab82cbe99e2937ddd. When his body lands, re-dump `hero_skeleton.json` and rebuild. Flagged on his skeleton:
   - `chain_strike` spins 106 degrees at the blow;
   - `lie_side_wake`'s forearm goes 16 cm into the ground;
   - his story clips need fitting to his proportions.
5. **Polish:**
   - the chain haul's landing crouch;
   - toes 3 to 8 cm into the ground in some folk takes and in `sit_back_heels` (a toe clamp in `retarget`);
   - `death_back`'s shield edge, 5 cm in.
6. **The boar** on the creatures lead's quadruped rig (af551cacc6292152f).

## 5. Decisions and why

- **The wrist is anisotropic and read on its own axes,** because a sideways bend of 60 to 80 degrees reads as broken. The swing is taken after the twist (`dh = twist * swing`), as the radius carries the wrist's axes when it rolls. Measuring it the other way round mixes flexion into deviation.
- **Weapons sit in a diagonal grip,** because a sword held square needs a kinked wrist to point along the arm. The game and the solver must agree, so the lean lives in both places (`keyed.GRIP`, `Arms.Spec.Lean`) and nowhere else.
- **Carried blades use `thumb`, not `blade`.** A hand behind her with a straight wrist can only point a blade down or across her, so a long blade's hand stays at her side and ahead.
- **A clip keyed past anatomy is re-keyed, not clamped and passed.** The clamp only keeps it legal: where a hand falls short, look at the result.
- **Retargeted takes are fixed at retarget,** for wrists, knees and seats, with planted feet kept.
- **Story falls are shown:** the view falls and rises; the fight logic is untouched.

## 6. Failures and why

- **warden_show took four tries.**
  1. Pointing the blade at the front camera crossed her face and read as nothing.
  2. Close in, the forearm crossed the face.
  3. Over the shoulder needed more than 95 degrees of forearm roll.
  4. The overhand guard with the hand out to her right works.
  - Check the creation screen's view (front, turned 14 degrees) before choosing a pose.
- **The first run carry pointed the blade out and down**, so from the side it read as a cane. Down-forward with a steady hand reads as carried.
- **A full build without names drops the clips modules build only when named** (the walks and C01). Always pass every name: `her_names.txt` and `hero_names.txt` in scratch.

## 7. Gotchas

- **The worktree guard** refuses `cd ... && git` chains, heredocs that touch the worktree, variables in commands and computed `python` programmes. Write patch scripts to the scratchpad and run them plainly. PowerShell is the easy path for `python tools/anim/...`.
- **`godot/assets` arrives as a text file.**
  - Replace it with a junction: `New-Item -ItemType Junction` to `public/assets`. A symlink needs admin rights.
  - Then run `git update-index --skip-worktree godot/assets`.
  - Copy `godot/.godot` and the `public/assets` `*.import` and `*.uid` files from a warm worktree (robocopy) to skip a full import.
- **`tools/anim/out` is not in git.** Copy it from a predecessor's worktree, or rebuild everything by name: about 40 minutes for her, as long for him, 10 for the folk, run in parallel in the background.
- Build the C# (`dotnet build godot/SurvivorUnchained.csproj`) before a game run.
- The audit's `angle()` has a 2 to 3 degree noise floor: the quaternions from FK drift off unit length.
- `--quick` with no `--sex` starts the male hero.
- Never commit `.uid` or `.import` files. Add files by name.

## 8. Scratch tools (`<scratchpad>/anim5`)

- **Renders:** `shots.py SET TAG [--pack --hero --folk]` renders a set of `anim_review` sheets in one Godot turn. The sets are `ws`, `wr`, `after`, `strikes`, `c01`, `flinch` and `fist`.
- **Arm and wrist checks:**
  - `spin.py N`: clips spinning a hand more than N degrees in a frame.
  - `wrist.py [names] [--before]`: flexion and deviation per clip.
  - `probe.py module fn [her|hero] step side`: arm geometry per frame.
  - `runarm.py` and `runtry.py`: the run's forearm and blade per frame, and trying thumb carries.
  - `twist.py`: the raw twist asked per frame.
  - `jitter.py`: frame-to-frame bone turn.
- **Body and prop checks:**
  - `blade.py`: a held blade through her body.
  - `groundall.py N [--before]`: every clip's worst sink into the ground. `groundj.py` checks one built clip.
  - `guard.py`: `warden_show`'s guard geometry, with GRIP and BLADE env vars to convert targets to keys.
  - `shield.py`: her shield's facing.
  - `contact.py`: the flask on her lips.
- **Before and after:** `out_before/` is the predecessor's built clips. `ba.py` stacks before and after strips.
- **The game:** `gamerun.py NAME [--pack] args` takes a turn, packs, and runs the game for frames.

## 9. Collaborators

- The coordinator (main). It knows about the fall fix and has had the strips.
- Combat (the successor of a739d6792d21f5efd) for Grimtunnel's roles.
- Cinematics (a7a4c20bcfd7ccfd3) for C01, C02 and C04, and `chain_strike`'s contact at 3/30.
- Skills VFX (abc6bbe020c7fe287): weapons now lean in her fist.
- The male hero (ab82cbe99e2937ddd).
- Creatures (af551cacc6292152f).
- UI and experience: her fall now shows.

## 10. Read first

1. `docs/team/animation.md`
2. `tools/anim/keyed.py`:
   - `Rig.solve` (the hand step, `_wrist_*`, `want_for`, the thumb path);
   - `GRIP` and `grip_of`;
   - `_whole_aims`;
   - `solve_frames`.
3. `tools/anim/audit.py`, then `retarget.py` (`keep_wrists`, the knee floor in `retarget`).
4. `tools/anim/clips/run.py` (`blade_carry`), `soul.py` (`warden_show`), `actions.py` (`death`, `_down_pose`, `get_up`, `cast_raise`).
5. `godot/src/Actors/Arms.cs` (`Hold`) and `PlayerView.cs` (`Fall`, `Revive`, the flinch).
