# Solver brief 5a: the axe swings, round 3 (the last) before judge r3 (animation 43, item 2)

Context budget: 240k. Spawn: su-lead-high, effort medium. Report in your FINAL message to animation lead 43, the lead that spawned you.

## Where and how
- Work in `.claude/worktrees/anim-40` (branch anim-40). godot/assets is a junction: never stash, reset --hard or checkout . there.
- Commit as you go and push. Never commit heroine.res, *_clips.json, manifest.json, arms_rest_godot.json or *.import.
- Turns go through tools/turn.py with --wait. Give a turn back the moment its job ends. Stop only PIDs you started. Never pack or shoot the male hero.
- Read `solver_atk_brief.md` only for "Where and how" and "The owner's bar".
- Solver 4's tools are in `solver_atk4/`: pf.py gives arm contact per frame, bite.py the axe's lowest point, exp.py and run*.sh try axe key variants, and chk/ holds the check outputs.
- `build.py --help` runs a FULL build. Don't call it.
- Test incrementally: rebuild, measure and shoot only the clips you change.
- Keep scratch in `solver_atk5/`.
- The clips are in `tools/anim/clips/axe.py`.

## Scope (yours alone)
Your clips: axe_fore, axe_heavy, axes_left and axes_right, standing and over the run (`--hold-base run_reaver@0.3`).
A second solver follows you on chain_strike, cast_flick and the runs: don't touch those.

## The judge's verdict
Read `judge_atk_r2_verdict.md`, all of it. It is short.
- Passed (keep them passing): fore0_m, fore3_m, heavy4_m, axesl3_m, axesr3_m, fore3_f45_m, heavy4_f45_m.
- Failed (yours): fore7_m, heavy0_m, axesr7_m, fore0_run_m, fore7_run_m.
- Known open: heavy7_m, heavy7_run_m.

## The job, in order
1. **Fix 3, her left hand off her hip** on fore and heavy, f3-f11, standing and running. It shows in most frames.
2. **Fix 4, a committed f7 finish** on fore and axes_right.
3. **Fix 5, the run-layer finishes clear her forward knee.**
   - Measure first, as the judge asked: the closest the axe comes to her left thigh and knee over the whole run cycle, not only at @0.3. Measure fore7_run and heavy7_run.
   - Heavy needs at least 10 deg more forward spine bend than fore, on the run layer too.
4. **heavy7 end-on**, using the judge's two lines in the verdict: roll the haft, keep it at least 30 deg below horizontal, and carry the head out to her left-front.
   - Then **fix 6, heavy f0 apart from fore f0.** After this, heavy must read heavier at f0, f7 and f7_run.
5. **Fix 7, fore and heavy f0:** the elbow up and back, and her face clear.
6. **Fix 8, the dual axes.**
   - Measure first: axes_left f0-f11, the closest the right haft comes to her head.
7. **Effort face (fix 10, low priority).** Only if the clips can already key an expression (grep axe.py and its helpers for a face or expression track). Otherwise skip it and say so in one line.

Keep solver 4's gains:
- Her right upper arm stays out of her breast: up/br at or below 41-51 mm.
- No new arm-into-body contact.
- hd (hand into her) on heavy stays at or below 66 mm.
- axes_left slide stays about 0.
- The finish still reads across.

The audit's borderline spins on the blow frames (f1-f3) are the blow itself: close them, unless your new keys make them worse.

## Acceptance and return
- motion.py --outfits on your four clips: no worse than solver 4's numbers in its chk/.
- audit: no new flags beyond the blow frames.
- fistfit axe: 21/21.
- Re-shoot to `tools/scratch/anim40/shots_atk5/`. The list is in `shots_atk5.txt` (write it from `shots_atk4.txt`): every fore, heavy and axes line, the `_f45` lines, and the three `_run_` axe lines.
- Make a half-size contact sheet for a working look (`python tools/half.py`).
- Return under 35 lines:
  - each fix: done or not, with numbers before and after;
  - the commits;
  - what's open.
