# Handoff: animation

For the next animation lead. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` ("Animation: joints and motion to perfection"), then this page, then `docs/team/animation.md`. Written by a9a80800a7dae2519 (branch `worktree-agent-a9a80800a7dae2519`), stopped early by the owner's usage wind-down on 6 October. Earlier leads: aa15f092820132274, a7dd95d00c4a6a017, a03acf30b3e9bdd70.

## 1. The owner's words and the brief

- "the motions that get scuffed are ... bad, unnatural movements with respect to wrists - follow through motion joint to joint, some elbow pinching or arms going through body or breast, some sliding. a lot is GOOD but we want perfection."
- The brief (from main):
  1. Audit every clip for her and the hero, in motion, at 1:1, jiggle on, in each of the four outfits. Measure wrists past natural limits, elbow volume loss, arm into torso and breast (against her actual mesh, not capsules), foot slide in cm per planted step, and overlap missing down the chain.
  2. Fix at the root, worst first: skinning (twist and helper bones, correctives), then rig and solver (wrist limits, elbow swivel, follow-through), then clip contacts and foot locking.
  3. Prove each fix with before and after numbers and a shot sheet.
- Coordinate weight changes with the outfits lead (afb34c385770877d3) and ask them to rerun the motion check. Rendering (a20bdef993e00f26b) owns how motion is drawn; joints are ours.

## 2. Measured so far, worst first

Run with `tools/anim/motion.py` (see 4). Only 6 of her clips have been audited; the full run was stopped at the wind-down.

1. **Elbows and knees fold.** The root cause: `build_heroine.py` folded AccuRIG's twist and share bones into the main bones (`FOLD`), so linear skinning has only two bones a joint.
   - Elbow region (8 cm either side) keeps 70% of its volume at a 90-degree bend, 59% at 120 and 53% at 145 (synthetic sweep).
   - In clips: run_warden 68/80% (l/r), sword_fore 67/80, cup_hands 73/75, cast_raise 79/80.
   - Knee: 66% in the run. Seen at 1:1 in `cast_raise`, where the elbow narrows to a deflated crease.
2. **Forearms wring.** The solver puts at least half of each wrist's turn into the forearm bone (`keyed.Rig.solve`, "share"), so the roll twists the elbow region: 25 to 48 degrees in the six clips. A ±80-degree turn costs the elbow 9% and the wrist 6 to 10%.
3. **Arms through her.**
   - run_warden: her left upper arm is 11 to 15 mm into the side of her chest (frames 0-5 and 16-21). Her hands pass through each other in front of her belly, up to 60 mm (frames 6-15). The shield hides this in play; it shows without one.
   - sword_fore: the follow-through drives the right forearm through the left hand (seen at 1:1).
   - cast_raise: the left forearm presses under her left breast (frames 9-12, seen).
4. **Sliding.**
   - In clips: warden_show's left foot glides 23 cm flat on the floor (frames 8-16, the creation screen) and 2 cm more (frames 51-66). run_warden slides 3.1 cm a step; sword_fore 1.1 cm.
   - In the game (read from `PlayerView.Carry`, not yet simulated): every start and stop slides. Between 0.25 and 2.2 m/s idle is blended with a run clamped to at least 0.55 of its rate. The view's speed lags the body twice over (the fight's 14/s, the view's 10/s). Turns pivot planted feet. There is no walk cycle and no foot lock.
5. **Wrists:** within range in the six clips (the predecessor's limits hold): idle_warden right ulnar 34, extension 42. The "correcting" motion is not yet isolated: look for wrists turning against the forearm's swing, and for flicks between frames.
6. **Overlap:** the metric exists (`motion.overlap`: hand lag after the upper arm stops) but is not yet summarised. By construction, the keyed arms move as one piece: IK each frame, with every joint on the hand's timing.

## 3. Done (committed; the helpers are off until verified)

- **Tools:**
  - `tools/anim/skin.py`: her glTF body and outfits skinned in Python exactly as Godot does, with a port of HerJiggle's springs. `ANIM_PEOPLE`, `ANIM_SKELETONS` and `ANIM_OUT` point it at a "before" copy.
  - `tools/anim/motion.py`: the audit. It measures contact against her real mesh, with each outfit's thickness laid on, the armpit apart, and a winding-number check; joint volumes; wrist bend and forearm roll; slide in cm per plant; and overlap lags. `--outfits`, `--hero`, `--save NAME`.
- **Helper bones**, 6 a side: `upperarm_twist_01`, `lowerarm_twist_01/02`, `upperarm_share`, `lowerarm_share`, `calf_share`.
  - `tools/anim/helpers.py` is the one spec. It also extends a skeleton, drives the bones, and splits weights as a field over space, so skin and garments split alike.
  - `tools/assets/heroine_rig.py` adds the bones in Blender and splits every mesh. It is hooked into `heroine_outfits.py` just before the body and outfit exports, and is **inert unless the build is passed `--helpers`**.
  - `godot/src/Actors/HerJoints.cs` drives them, as the last modifier, and does nothing on a body without them:
    - it hands the forearm bone's roll to the hand and shares the hand's turn along the forearm (0.4 and 0.8);
    - it half undoes the upper arm's turn at the shoulder;
    - each share bone takes half its joint's bend; the elbow and knee ones also swell across the bend (1/cos(bend/2), at most 1.5, along their own Z, which `heroine_rig` turns onto the hinge).
  - Wired into `People.Heroine` and `People.Hero`, `anim_review.gd` (`NOJOINTS=1` for before) and `lookdev.gd`, which also feeds the legal motion check. Data: `godot/art/people/rig_helpers.json`.
- **Prototype results** (current weights split in Python; not yet seen in Godot):

  | Measure | Before | After |
  |---|---|---|
  | Elbow volume at 90 / 120 / 145 degrees | 70 / 59 / 53% | 94 / 83 / 72% |
  | Knee volume | 75 / 65 / 59% | 101 / 93 / 83% |
  | Wrist under a ±80 turn | 90-94% | 98-100% |
  | Upper arm turned ±70 | 76-78% | 85-86% |
  | Arm raised 130 (shoulder share) | 73-81% | 95-107% |

  The 107% may read as a swollen shoulder: check it.

## 4. Next, in order

1. **Build and see the helpers.**
   - Take a Blender turn, then: `blender -b <main checkout>/tools/comfy/out/heroes/heroine_built.blend --python <wt>/tools/assets/heroine_outfits.py -- <wt>/godot/art/people/x --body <wt>/godot/art/people/heroine.glb --helpers`. It is long; scratch `build_body.ps1` wraps it.
   - Import, then re-dump `tools/anim/data/heroine_skeleton.json` (`anim_skeleton.gd`). The tools need the helper joints in it.
   - Check that `helpers.hinge_turn` on the built skeleton is about 0 for each share bone (the bulge then lies across the bend).
   - Render elbow, knee and shoulder sheets with and without `NOJOINTS=1`, at 1:1, and tune `bulge` and `amount` in `helpers.SPEC`.
   - Then measure each garment point's split against its nearest skin point; the outfits lead asked for this, so send it to them.
   - Then make `--helpers` the default, push, and ask the outfits lead to merge, rebuild and rerun the check.
2. **The full baseline audit**, before and after the helpers: `ANIM_PEOPLE=<before copy> python -u tools/anim/motion.py --outfits --save base`, then `--hero`. Use `python -u`: buffered output was lost at the stop.
3. **Solver and clips:**
   - arm clearance against her mesh: an SDF of trunk and breasts, with outfit cover and a jiggle margin, in the chest's frame; swivel the elbow first, then push the hand;
   - follow-through as a post-pass: lag and overshoot down shoulder, elbow, wrist and fingers, held off where hands hold or touch;
   - foot locking in clips (warden_show first);
   - the wrist's "correcting" motion.
4. **In the game:**
   - a stride simulator of `PlayerView.Carry` (starts, stops, turns);
   - then a walk cycle, a run rate from the body's own speed, and a runtime foot lock.
5. **The hero:** the same helpers in `hero_male_body.py` (with ab82cbe99e2937ddd), then his audit.

## 5. Decisions

- **Bones, not blend shapes, for joints.** Garments take bones through their weights. Correctives would need a copy for every garment.
- **The driver unrolls the forearm bone whatever the clip did**, so library clips and retargets are fixed too. A shield on the forearm will then keep only the forearm's hinge: mount it on `lowerarm_twist_02` once the helpers are in, so it turns with the radius.
- **The weight split is a field over space**, the same for skin and every garment.

## 6. Gotchas

- The worktree guard refuses `cd && git` chains, `xargs`, and heredocs that touch git. Write scripts to the scratchpad.
- In `anim_review.gd`, the shield stand-in (a 60 cm disc) hides her torso. Use `OUTFIT=none` and `WEAPON=sword` to see arms against her body.
- In Blender, a new EditBone needs a length before `.matrix` takes.
- Scratch tools are in `<scratchpad>/a6` (not kept): `batch.py` (sheets in one Godot turn), `crop.py`, `wax.py` (a quick numpy render), `t_helpers.py` (the volume sweep), `dbg_contact.py`, `dbg_slide.py`.

## 7. Collaborators

- The outfits lead (afb34c385770877d3) agreed the hooks stay on this branch. They want the garment-against-skin split measured. Their motion check builds from `lookdev.gd`.
- The rendering lead (a20bdef993e00f26b); the hero (ab82cbe99e2937ddd).

## 8. Read first

1. `tools/anim/helpers.py`
2. `godot/src/Actors/HerJoints.cs`
3. `tools/anim/motion.py` and `skin.py`
4. `tools/anim/keyed.py`: `Rig.solve` (the twist "share"), `solve_frames`, `build`

HANDOFF READY: docs/handoff/animation.md on worktree-agent-a9a80800a7dae2519 (commit below)
