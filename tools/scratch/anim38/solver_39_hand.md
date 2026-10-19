I've built the fix the judge asked for: the left hand now lies on the knee instead of hanging beside it. One part of the brief can't be fully met: no single pose rests the palm on both the reaver and bare skin, so I've given the gap per outfit below. One commit on `anim-38`, `d6363891`, not pushed. Only `tools/anim/clips/soul.py` changed; heroine.res, hero.res, *_clips.json, manifest.json and arms_rest_godot.json are not committed. I shot no pictures, and heroine.res is not repacked, so it needs a pack before you shoot.

## What changed
A new function, `knee_hand`, places the left hand every frame from f58 to f107. It solves her legs at that frame and puts the palm on the top-outer face of the left thigh.

- **Way down:** the hand leaves the stock along the idle's own lift (f55-59), so the pinky clears the crossbow. It turns palm-down by f62, is laid on the thigh by f64, and slides forward to the kneecap by f70. Its height drops from 1.6 cm over the reaver at f69 to 0.2 cm by f75, which is the settle.
- **Bottom f75-90:** it holds. Fingers in the soft relaxed curl, tilted 16° down over the front of the knee.
- **Way up:** from f90 the palm lifts and slides back toward the hip as she rises, so the arm never straightens (no push-off). It returns to the stock f101-114 as before.
- **Constants:** the new ones are `KNEE_MIX`, `KNEE_TURN`, `KNEE_T`, `KNEE_LIFT`, `KNEE_OUT`, `PALM_R`, `PALM_TILT`, `PALM_FWD/PALM_UP`, `KNEE_POLE` and `KNEE_CURL`. `PALM_R` is the measured top of the thigh along its length, for the thickest outfit at each point. I removed `BREAK_BY_KNEE_L`, `BREAK_WIDE_L`, `VW`, `VC`, `reach_l`, `turn_l` and the "open" fingers.

## Numbers (before → after)
- **Build:** clean, 121 frames.
- **motion.py --outfits:**
  - Skin columns: 0 on both sides, before and after.
  - Left outfit columns: 0/0/0/0 → 0/0/1/0 mm (reaver 1 mm, within the 2 mm limit).
  - Right: warden 9, arcanist 0, reaver 18, ranger 0, unchanged.
  - Foot slide: 0.0/0.4 cm, unchanged.
  - Not in the acceptance list: the left elbow volume minimum went 90 → 86%, and wrist extension 39 → 34°.
- **ev.py:** crossbow into her 0 → 0, arms 0/0, left-hand gap minimum 2.9 mm (the same). On the way there it hit 0.6 mm into her left pinky at f57; straightening the fingers through the lift fixed it.
- **audit.py:** nothing flagged on the heroine's `idle_stalker_break`; 221 flagged frames in total, unchanged.
- **fistfit.py crossbow:** 8 frames, 0 failing.
- **Palm-to-outfit gap at the bottom (f75-90),** palm / fingers:

  | | palm | fingers |
  |---|---|---|
  | reaver (thickest) | +1 to +2 mm | +19 mm |
  | warden | 27 mm | 31 mm |
  | arcanist | 33 mm | 40 mm |
  | ranger | 40 mm | 49 mm |
  | bare skin | 46 mm | 51 mm |

  - **Why the thin outfits sit high:** most of the outfits have a pad over the kneecap (reaver 3.2 cm, warden 2.0, arcanist 1.2, ranger 0.2 cm). Sitting on the reaver's pad therefore leaves at least about 3 cm over bare skin, and the shape of the palm adds about 1.4 cm.
  - **The alternative I rejected:** I tried putting the palm on the thigh just above the knee, where every outfit's cover is about 0. That bent the elbow to 97°, so I kept the kneecap.
- **Whole move, f62-104:** nothing goes into any outfit (minimum about 0 mm). While it slides along the thigh the palm rides 2-5 cm over the skin; the reaver's fingers are the binding point at f65-66 and f94-98.
- **Lateral (hand's outward distance from the left shoulder, her space):**
  - f56-70: worst +13.7 cm → +7.0 cm (f67).
  - f95-112: worst +13.4 cm → +7.5 cm (f102).
  - The old 30 cm swing round the knee is gone; the hand now stays over the thigh.
- **Arm at the bottom:**
  - Elbow bend 72-74°, a little over the 45-70 asked. It is 50° at landing (f69) and peaks at 84° as she rises (f93-96).
  - The elbow points out (11.5 cm outside the shoulder) and slightly forward (+2 cm); at f96-102 it is 13-16 cm back.
  - Upper arm about 27° out from the chest (idle is 10.5°). I took the judge's "under 10°" as the hand's path, which stays within 8 cm. Pointing the elbow back further would cut that angle.

## For the judge to look at
- **The gap over thinner outfits:** 3-4.6 cm over bare, ranger and arcanist knees. It may read as the hand hovering from the side; from above it should be hidden under the palm.
- **The slide:** the palm rides 2-5 cm above the thigh between f63 and f68.
- **The shoulder sweep:** the shoulder does not follow the head sweep, because I added no collarbone keys.

The measuring scripts are in `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\8f465914-1835-4dd3-9037-c20af604bc43\scratchpad\anim39\hand\`. `g3.py` gives palm and finger gaps per outfit per frame, `arm.py` the elbow and shoulder angles, and `prof.py` the thigh's surface height with each outfit's cover.

The changed file is `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim\clips\soul.py`.