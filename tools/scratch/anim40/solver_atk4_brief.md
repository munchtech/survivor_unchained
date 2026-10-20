# Solver brief: her attack poses, round 3 fixes before judge r2 (animation, item 2)

Context budget: 220k. Spawn: su-lead-high, effort medium (coding). Report in your FINAL message to the animation lead that spawned you, not to the coordinator.

Read `tools/scratch/anim40/solver_atk_brief.md` ("Where and how", "The owner's bar") and `solver_atk3_brief.md` (the job and its numbers, which still hold). Work in `.claude/worktrees/anim-40` (godot/assets is a junction: never stash, reset --hard, checkout .). Commit as you go; never commit heroine.res, *_clips.json, manifest.json, arms_rest_godot.json, *.import. Turns via tools/turn.py; stop only PIDs you started; never pack or shoot the male hero. Test incrementally: rebuild and re-shoot only what you change.

## Solver 3 built (58512dec, 48d41e2b, c3234c87, eb3d732f)
- Stance on (meta "stance": True) for axe_fore, axe_heavy, axe_back, axes_left/right/heavy and cast_flick: feet 1.31x shoulders, left foot 20 cm ahead, knees 12-21 deg, no knock-knee, pelvis -13/+23, hinge 14 (heavy 25). Measure: `solver_atk3/stm.py`.
- Finishes go across: the right fist ends level with her left thigh, and the axe head ends 51-54 cm clear of her leg. axe_fore f0 is cocked. cast_flick's free hand starts low, and the wand elbow is soft.
- chain_strike settles 4 cm over f6-f9, the free arm stays back, and the head is planted f3-f9. Tools: `solver_atk3/rsearch.py`, `wsearch.py`, `lfit3.py`; outputs in `solver_atk3/cs/`.
- Checks (`solver_atk3/chk/`): motion_base.txt (before) vs motion_new.txt (after); audit, arms_*, fist_* (fistfit passes). Shot list `shots_atk3.txt`; contact sheet contact_atk3.jpg. NOT judged.

## The job, in order (no judge sees these frames until 1-3 are fixed)
1. **Her right upper arm into her breast: 72-80 mm on the stance finishes (it was 44-66).** motion `r: up/br`: axe_fore 44->72, axe_heavy 43->68, axes_right 45->72; on the left, axes_left 51->75. The cause is `clav_r=(4, 22..24)` on the finish keys in `clips/axe.py` (lines ~94-180). Fix: less clavicle forward (try 10-14), turn the chest a few more degrees into the blow instead, and move the elbow pole out and down so the upper arm passes in front of the breast rather than through it. The finish must still read across (fist level with her left thigh, head 15 cm+ outside her leg). Target: br and up at or below the old 41-51; outfit columns (war/rea/arc/ran) no worse than the before numbers.
2. **axe_heavy must read apart from axe_fore at the finish** (the judge: "fore and heavy look alike"). Heavy: about 10 deg more hinge, the head about 15 cm lower and further out, a deeper knee, a longer hold. Note that heavy's hd (hand into her) went from 66 to 80: bring it back to 66 or below.
3. **chain_strike, two hands: ONE round only, then restage (the coordinator).** Solver 3 found two hands at a 50 deg haft only fit with her left upper arm 80 mm into her trunk; its new f9 key puts the left hand 14-51 mm into her thigh, and the head sinks 4-7 cm at f10-11 (fix both). Try first (with numbers): a different left-fist roll with a re-fitted L_WRAP, or the haft at 20-25 deg (rsearch/wsearch). If two hands can't be made clean within about a third of your budget, **restage the strike so both hands read naturally**: a two-handed overhead chop that lands centred in front of her (both arms forward, symmetric, the left hand at the haft's butt and the right hand higher up), not off to her right side where the left arm has to cross her trunk. Two hands on the haft is a must (the owner). Left fist gap to the haft at most about 8 mm on every frame where it holds (3.6 px/cm at the 0.6 zoom). Slide no worse than 13.4/17.0 (it's now 15.8/19.6; it was keyed before, so check the feet).
4. **The runs (solver 3 job 5, untouched):** run_arcanist_wand and run_reaver_axes, the free hand's forward extreme at the front of her left hip, 10-12 cm+ from the midline (solver 1's `solver_atk/runhand.py`); wand run a loose fist; the second axe's head trails back and down outside her left thigh. Legs byte-identical; sprints follow.
5. **The audit's 3 borderline spins:** clear them or say why they're the blow itself.

## Acceptance
motion.py --outfits on the changed clips: no new arm-into-body contacts, br/up back to the before numbers or better, no worse slide. audit: no new flags. armscheck axe/wand as before. fistfit axe 21/21, wand 3/3. Re-shoot `shots_atk3.txt` (plus chain_strike f0/f3/f6/f9 and the three runs) to `tools/scratch/anim40/shots_atk4/` and make a half-size contact sheet for a working look only.

## Return (under 40 lines)
What changed per clip, before/after numbers (br/up, hd, slide, the chain gap), the commits, the shot folder, what's open and why.

## Note from animation 43 (19 Oct, night)
Integration merged at a40cba09. The local pack by-products (heroine.res, heroine_clips.json, manifest.json, arms_rest_godot.json) were restored to integration's (89 clips, no stance clips packed); a copy of solver 3's local pack is in the coordinator scratchpad `anim43/prepack/`. Re-pack her library once before your first measure or shot, so solver 3's stance keys are in it. Turns: `take blender`/`take godot` with --wait, give back at once. Keep each wait under an hour.
