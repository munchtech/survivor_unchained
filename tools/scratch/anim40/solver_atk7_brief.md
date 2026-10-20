# Solver briefs 7a/7b/7c: the restage round (round 4, the LAST; animation 43, item 2)

Spawn each on su-lead-high, effort medium, with Context budget 200k. Report in your FINAL message to animation lead 43, the lead that spawned you.

**The hard stop (the coordinator).** After this round's judge, anything that still fails the gate is CUT: it falls back to the clip it replaces, or it is gated off. There is no fifth round. If you see an item can't get there, stop on it early and say why. Don't spend your budget on it. Do the items in the order given.

## Where and how (all three)
- Work in `.claude/worktrees/anim-40` (branch anim-40). godot/assets is a junction: never stash, reset --hard or checkout . there.
- Commit as you go and push. Never commit heroine.res, *_clips.json, manifest.json, arms_rest_godot.json or *.import.
- Take turns with tools/turn.py --wait, and give them back at once. Stop only PIDs you started. Never pack or shoot the male hero.
- `build.py --help` runs a FULL build. Don't call it.
- Rebuild, measure and shoot only your clips.
- Read `solver_atk_brief.md` "Where and how" for the build, shoot and measure commands. `shoot.sh <list> <out>` shoots a list.
- Read `judge_atk_r3_verdict.md` (short): your calls are numbered there.
- Play truth (solver 5a):
  - In play, a swing takes the pelvis from the idle or the run, so `hinge` never reaches the screen. Lean comes from spine pitch and roll.
  - A stance-marked clip (axe_fore, axe_heavy, axes_*, cast_flick) plays its OWN legs while she stands and the run's legs while she moves. chain_strike is a whole-body clip.
  - Measure play-true: `solver_atk5/m5.py`, `solver_atk4/pf.py` (arm contact per frame), `solver_atk5b/cm.py`, `fk.py`, `solver_atk6/lh.py`.
- Acceptance on your clips:
  - motion.py --outfits: no new arm-into-body or axe-into-leg contact, and no worse slide;
  - audit: no new flags beyond the blow frames;
  - fistfit: axe 21/21, wand 3/3.
- Re-shoot ONLY the frames named in your part to `tools/scratch/anim40/shots_atk7/`, with each line copied from shots_atk5.txt or shots_atk5b.txt (atk6 for the `_m` runs). Make a half-size sheet `contact_atk7<x>.jpg` for a working look.
- Return under 30 lines: each call, done / not done / cut-recommended, with numbers before and after; the commits; what's open.

## 7a: the axe swings (tools/anim/clips/axe.py). Calls 1-5.
Frames: heavy0_m, heavy7_m, axesr7_m, fore7_m, fore0_run_m, fore7_run_m, heavy7_run_m.
fore7_m passed. Keep it passing: only the head changes on it.

Order:
1. **Call 2, the head roll onto her right shoulder at every f7 finish (fore, heavy, axes_right, and the run versions).** Find where it comes from first: the spine roll solver 5a added (-16 toward her left), a neck or head key, or play's HeadLevel. Measure the head roll per frame, play-true, then bring it to 5 deg or less over f5-f11. On heavy, also bring the chin up about 10 deg.
2. **Call 5, the run-layer finishes:** the fist beside her left hip from the 315 camera, never over her crotch, with the head trailing outside her thigh.
3. **Call 4, fore0_run's left arm.**
4. **Call 3, axesr7's left axe:** hold the f3 shape.
5. **Call 1, heavy0's loaded legs.** These are the stance clip's own legs, keyed in the clip.

## 7b: chain_strike (tools/anim/clips/arts.py) and cast_flick (tools/anim/clips/actions.py). Calls 6 and 7.
Frames: chain3_m, chain6_m, chain9_m, chain3_p (passed: keep it), flick4_c, flick8_m, flick4_run_c, and flick0_m and flick1_m (passed: keep them).

1. **Call 7, cast_flick:**
   - the free arm close to her side, with a soft elbow;
   - the f8 reach at lower-chest height;
   - the f4 wand no lower than 25 deg below level.
   - Check that the wand never goes through the hat.
2. **Call 6, chain_strike f3-f9:**
   - the feet wider, so both shins show from 315;
   - the hips lower;
   - the head closer, with the haft at 50-55 deg;
   - the hands at mid-shin, and the chin up.
   - Keep: two hands on the haft (0-2 mm, f3-f9), the head planted, no ground contact before f3, and the slide at 13.6/16.5 or better. Measure the side spread of the feet and the hip height, as the judge asked.

## 7c: the runs (tools/anim/clips/run.py, solver 6's WAND_L and AXES_L). Calls 8 and 9.
Frames: wrun_c, wrun_m, axrun_c, axrun_m, and the passed wrun_p and axrun_p (keep them).
The legs stay byte-identical, and the sprints follow.

1. **Call 8, run_arcanist_wand:** the free fist's forward extreme at lower-rib height, under the bust and at least 10 cm in front of it, with the elbow at about 85 deg. Keep the 25 cm lateral offset. The back extreme goes behind the hip. Measure the fist height at the forward extreme against her navel.
2. **Call 9, run_reaver_axes RESTAGE:**
   - the second axe hangs at her side, with the elbow at about 150 deg and the upper arm about 10 deg out;
   - the haft trails 15-20 deg back from vertical, so the head sits beside or behind her calf and never forward of her knee;
   - the edge faces back;
   - the swing is about ±20 deg, with the fist never more than 15 cm forward of her hip crease.
   - Measure over the cycle: the head's distance to her knee, her shin and the back-kicked foot (at least 10 cm).
   - If the wrist limits can't reach this, say so early. The fallback is cut: run_reaver_axes then plays run_reaver's arms with the second axe sheathed or stowed, so name the cheapest such fallback.
