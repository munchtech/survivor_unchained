I rebuilt the bottom of `idle_stalker_break` as a one-knee kneel, and every number in the brief passes. Two commits on `anim-38`, not pushed:

- `17530f7c` restages the clip on one knee.
- `8bc80788` keeps the left hand closer to her body on its way past the knee.

Only `tools/anim/clips/soul.py` is committed. heroine.res, hero.res, *_clips.json and manifest.json are not.

## The left hand rests beside the knee, not on the ground
With her back near upright, the ground is out of reach. Her shoulder is about 0.95 m up and her arm is about 0.58 m long. So the hand takes the brief's fallback, with one change. It doesn't sit on top of the knee: laid there, it went 6 to 127 mm into the leg pieces of all four outfits. It hangs open just outside and ahead of the left knee, fingers toward the ground, about 15 cm out from the knee joint. On the way down and back up it goes round the outside of the knee, which rises under it.

## Numbers (before → after)
- **Build:** `python tools/anim/build.py idle_stalker_break --no-pack` builds clean (121 frames, 4.00 s).
- **motion.py --outfits:**
  - Skin columns up/fa/hd/br/pit: 0 on both sides, before and after.
  - Left outfit columns: 0/0/0/0 → 0/0/0/0.
  - Right: warden 11 → 9, arcanist 0 → 0, reaver 20 → 18, ranger 0 → 0.
  - Foot slide: 0.1/0.0 → 0.0/0.4 cm (left/right).
- **ev.py:** crossbow into her 0 → 0, both arms 0 → 0. The left-hand gap is 2.9 to 352 mm (was 3.4 to 267), and its minimum is the hand resting on the stock outside f56-111.
- **Feet:** the left foot's ball doesn't move in any frame. The right foot's ball holds still while she is on it (f67-97). motion.py measures the right sole's worst slide at 0.4 cm while planted, and nothing at home.
- **Right knee at the bottom:** the joint sits at 4.8 cm, the standard knee-on-ground height the other kneels use. The lowest knee skin is 0.6 cm above the ground (f73-90): within 2 cm, and not through it.
- **Bottom frame (f81):**
  - Spine angle from vertical (pelvis to neck): 55.3° → 18.3°.
  - Shoulders ahead of the pelvis: +0.356 m → +0.134 m.
  - Head facing: 63.8° below level → 30.4° below, so up 33°. It sweeps from 10° to her right to 12° to her left across the hold.
  - Pelvis height: 0.689 → 0.545 m.
- **stance.py:** pelvis_y 0.909 [0.545..1.064], pel_fwd 0.071 [-0.031..0.292], trunk 14.4.
- **feet.py:** stagger +0.061 → +0.340 m; this is the average over the clip and rises because of the step back. Ankle width is 0.219.
- **audit.py:** nothing flagged on the heroine's `idle_stalker_break`.
- **fistfit.py crossbow:** 8 frames, 0 failing.

## What changed in `stalker_break`
- **Right foot:** a small function places it frame by frame:
  - Heel up f54-57.
  - Swing back f57-67 to its tucked toes (foot pitched 50°, toes bent 54 so they lie near level).
  - Held there; it leaves at f97 and is home at f108.
  - Each swing lifts straight up first and sets straight down last. Before that change it slid 2.9 cm on landing.
- **Right knee:** placed one thigh-length below the solved hip at the bottom, with the foot one shin-length behind it. The leg's bend direction turns onto that spot over f57-67 and back over f97-104.
- **Pelvis:** keyed in her own space, with the base idle's sway subtracted so the knee stays still: shift f54-57, touchdown f67, bottom f73-90, off the knee f97 with the back leg near straight, foot home f108, standing f114. A monotone spline joins these points so held positions don't overshoot.
- **Upper body:** keys at the bottom (f73, f90) plus a forward lean over the left foot at touchdown and lift-off (f67, f97). The glance keys before f56 are untouched.
- **Hand timing kept:** the left hand still comes off the stock at f55-59, takes the open hand at f56 and is back on the stock at f108-114. The right hand is home at f110.
- **Crossbow:** goes out to her right first (f61 and f101), then is held low ahead. Its aim is straightened (`BREAK_AIM_R`) because aiming it across her put it 7 to 21 mm into her left shin.
- **New constants:** `BREAK_PELVIS` (0.02, 0.545, -0.38), `BREAK_KNEE_X` -0.10, hips/spine/neck/head `(0,4,0)`/`(0,8,0)`/`(0,2,0)`/`(-10,15,0)` turning to `(12,17,0)`. Also `BREAK_BY_KNEE_L`, `BREAK_WIDE_L`, `BREAK_FWD_R`, `BREAK_HAND_R`, `BREAK_AIM_R`, `TUCK_PITCH`, `TUCK_TOE`, `BREAK_LEAN`, `BREAK_DOWN/OFF/UP`, `R_HEEL/R_BACK/R_HOME/R_DOWN/R_STAND` and `KNEE_AIM`.
- **Removed:** `STALKER_CROUCH_L`, which nothing else used.

## Side view (Godot)
I shot four frames in one godot turn: a side view at 2.7 s, the play camera at 2.7 s, and side views at 2.13 s and 3.33 s. In the side view at the bottom the kneel reads clearly: right shin flat behind her, left knee up, back upright, head up.

At f62-66 and f97-101 the left hand swings about 30 cm out to her left. From above, that looks like a hand flung out for balance. Narrowing that path further brought back collisions with the knee, so judge it at 1:1. These shots haven't been through a judge.

## For you to know
- **The step back is long:** the right foot goes about 0.85 m back, and each swing takes 10-11 frames. That distance is what a real kneel needs at her leg lengths (thigh 0.49 m, shin 0.45 m), but with only f56 to f73 to get down, the step is quick.
- **heroine.res is packed with an older build:** the shoot script repacked it before the final tweak to the hand's path, so it lags `8bc80788` by that tweak. A full pack is needed before any further shots.
- **Uncommitted file I didn't check:** `tools/anim/data/arms_rest_godot.json` shows as modified in the worktree. Possibly the shoot's import rewrote it, but I didn't confirm; I left it alone.

Scratch scripts and shots are in `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\8f465914-1835-4dd3-9037-c20af604bc43\scratchpad\anim39\brk\`:
- `shots\brk_side.png`
- `shots\brk_play.png`
- `shots\brk_down.png`
- `shots\brk_up.png`

The changed file is `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim\clips\soul.py`.