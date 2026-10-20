# Solver brief 5b: chain_strike, cast_flick and the runs, round 3 (the last) before judge r3 (animation 43, item 2)

Context budget: 240k. Spawn: su-lead-high, effort medium. Report in your FINAL message to animation lead 43, the lead that spawned you.

## Where and how
- Work in `.claude/worktrees/anim-40` (branch anim-40). godot/assets is a junction: never stash, reset --hard or checkout . there.
- Commit as you go and push. Never commit heroine.res, *_clips.json, manifest.json, arms_rest_godot.json or *.import.
- Turns go through tools/turn.py with --wait. Give a turn back the moment its job ends. Stop only PIDs you started. Never pack or shoot the male hero.
- `build.py --help` runs a FULL build. Don't call it.
- Test incrementally: rebuild, measure and shoot only your clips.
- Keep scratch in `solver_atk5b/`.
- Read `solver_atk_brief.md` only for "Where and how" and "The owner's bar".
- Tools you can reuse:
  - solver 4: `solver_atk4/` (pf.py arm contact per frame, cs.py and p/*.py for chain_strike variants, flat.py, chk/);
  - solver 3: `solver_atk3/` (stm.py stance measure, rsearch.py, wsearch.py, lfit3.py);
  - solver 1: `solver_atk/runhand.py`;
  - solver 5a: `solver_atk5/m5.py` (play-true pose measures).
- Solver 5a found that, as play shows a swing, the pelvis comes from idle or run, so `hinge` never reaches the screen and any lean has to come from spine pitch and roll. Check how each of your clips actually plays before keying: chain_strike is a whole-body clip, and cast_flick is a stance swing.

## Scope (yours alone)
Your clips: chain_strike (`tools/anim/clips/arts.py`), cast_flick, and the runs' free hand (run_arcanist_wand, run_reaver_axes).
Solver 5a has finished axe_fore, axe_heavy and axes_left/right (commits 4f892edc, f830d3ab). Don't touch them.

## The judge's verdict
Read `judge_atk_r2_verdict.md`. It is short.
- Passed (keep them passing): chain3_p, flick0_m, flick1_m, flick4_c, flick4_run_c.
- Failed (yours): chain0_m, chain3_m, chain6_m, chain9_m, flick8_m.

## The job, in order
1. **chain_strike, restaged (fixes 1 and 2).**
   - **The wind-up, f0-f2:** she stands, two hands overhead, the head of the axe behind her crown. No knee and no hand touches the ground.
   - **The strike, f3-f11:** knees out over the toes, the torso at about 45 deg (not horizontal), her head above her shoulder line, and her elbows opened so the push runs down the haft.
   - Keep what solver 4 achieved:
     - the left fist 0-2 mm on the haft;
     - the head planted;
     - the flat toward the camera;
     - no arm into her body.
   - The left hand joined the haft in one frame (f2-f3, a 48 deg spin). With two hands from f0 this goes away: confirm it in the audit.
   - **Slide:** 15.8/19.6 against a target of 13.4/17.0, from the feet drifting during the recovery after f10. Fix it if you can.
   - **Measure, as the judge asked:** hip height and ground contacts over f0-f3.
   - The front loincloth panel is the outfit area's problem (routed). Don't chase it, but don't make the crouch deeper than the judge asked.
2. **cast_flick (fix 9).**
   - **f8:** the wand reaches toward the target (elbow about 150 deg, wand 10-15 deg below horizontal), the free hand near her hip or up at her ribs, knees about 15 deg with her weight on the front foot.
   - **f0:** the wrist back about 45 deg, so the tip points back over her right shoulder.
   - Check that the wand never goes through the hat.
   - Measure, as the judge asked: f0 and f8 foot spread and knee angles, against axe_fore's stance. The judge saw her legs straight and nearly together at f0 and f8 even though the clip is stance-marked. Find out why.
3. **The runs (round 1's failure, never fixed): run_arcanist_wand and run_reaver_axes.**
   - The free hand's forward extreme sits at the front of her left hip, 10-12 cm or more from the midline (measure with runhand.py). Neither hand should be at her midline or groin.
   - In the wand run, the free hand is a loose fist.
   - The second axe's head trails back and down, outside her left thigh.
   - The legs stay byte-identical, and the sprints follow.

## Acceptance and return
- motion.py --outfits on your clips: no new arm-into-body contact, and no worse slide.
- audit: no new flags.
- armscheck: wand as before.
- fistfit: axe 21/21, wand 3/3.
- Re-shoot to `tools/scratch/anim40/shots_atk5b/`. Write `shots_atk5b.txt` from `shots_atk4.txt`, with these lines:
  - every chain line (chain0, 3, 6, 9 _m and chain3_p);
  - every flick line;
  - flick4_run_c;
  - wrun_c and axrun_c;
  - a `_p` play-camera line for each of the two runs.
- Make a half-size contact sheet for a working look.
- Return under 35 lines:
  - each fix, with numbers before and after;
  - the commits;
  - what's open.
