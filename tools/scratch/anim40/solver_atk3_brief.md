# Solver brief: her attack poses, round 2 (animation, item 2)

Context budget: 220k. Report to the animation lead that spawned you (its id is in your spawn message), not to the coordinator.

Read `tools/scratch/anim40/solver_atk_brief.md`, sections "Where and how" and "The owner's bar". They give the worktree, the safety rules, the build, shoot and measure commands and the bar, and they still hold. Round 1: solver 1 (1d6bea5e, 37fbc052) and solver 2 (78cc822e, 0a408ad0), judged in shots_j1. The max judge's verdict is summarised below. Its frames are in `tools/scratch/anim40/shots_j1/`, with the list in `shots_j1.txt`. Of 23 frames, 10 pass: every mid-swing frame, run_c, run_m and chain3_p.

## New since round 1 (commit 7f087c06): stance swings
A clip whose meta has `"stance": True` now plays on her WHOLE body while she stands (PlayerView.UpperHer, through FullHer with soft=true). It uses its own keyed feet and hips, and fades into the run the moment she moves. While she moves, the clip still rides her upper body over the run.
- `--hold` shows a stance clip on its own legs, head level.
- `--hold-base run_reaver@0.3` (an extra arg; add it to a shot line's QUICK field, or put it in a variant of shoot.sh) lays a swing over the run's legs. That's the moving case, the one the player sees most in a survivors-like.
So the keyed legs and hips in `clips/axe.py` (`feet()`, `hips_yaw`, `weight`, `pivot`) now reach the screen whenever she stands.

## The job
1. **Stance on (axe.py: axe_fore, axe_heavy, axe_back, axes_right, axes_left, axes_heavy; actions.py: cast_flick):** set `"stance": True` in each build's meta and key the stance (judge's numbers):
   - feet about 1.3x shoulder width, the left foot about 20 cm forward, knees bent 15-20 deg, never knock-kneed (knees over the toes);
   - the pelvis turned about 15 deg back at f0 and 20-25 deg into the blow by f7;
   - a 10-15 deg hinge from the hips at the finish, the back long and the head up (play levels the head; the hunch must not come back);
   - the feet planted through the swing: run motion.py's slide on these clips, and no new sliding.
   cast_flick's stance is lighter: a caster's step, weight forward into the flick.
2. **Finishes (axe_fore, axe_heavy, axes_right, and axes_left mirrored), f7 on:**
   - carry the right hand across to in front of her left hip or upper thigh, about 25-30 cm left of where it ends now and 10 cm forward, arm long;
   - roll the right shoulder forward about 20 deg, chest turned 20-25 deg left;
   - the axe head ends OUTSIDE her left leg, at least 15 cm clear on screen at the 0.6/315 camera, haft about 30 deg below horizontal (it now sits on her left boot top);
   - axe_heavy: about 10 deg more hinge and the head about 15 cm lower and further out than fore, so the two read apart;
   - the free left arm (fore and heavy) long (elbow 140-150 deg) and swung 20-30 deg behind the torso as the counterweight, not winged out.
3. **axe_fore f0:** cock it as axe_heavy's f0 does: right hand beside or behind the right ear, elbow up and back, axe head back over the right shoulder (haft 30-45 deg behind vertical), shoulders turned about 25 deg back from the hips (it now reads as raising a torch).
4. **cast_flick:**
   - f0: the free left hand starts low at her left side (elbow about 30 deg, hand at hip height, about 10 cm off the thigh). No chest clutch: it cups under her right breast now, and the hand snaps about 40 cm by f1.
   - f4-f8: bend the wand elbow 15-20 deg, not locked, the arm forward of her shoulder line; the free arm about 15 deg off her side (now 40), fingers relaxed and curled, not splayed.
   - The wand stays clear of the hat (solver 2 fixed f0: keep it).
5. **Runs (clips/run.py, the RUNS `swing=` override solver 1 added):** run_arcanist_wand and run_reaver_axes still bring the free hand to her midline (wand: an open flat hand on her lower belly; axes: the second axe's fist at her navel, its haft toward her groin). Move the left hand's forward extreme to the front of the left hip, 10-12 cm or more from the midline (as run_reaver now does), with about 15-20 deg less shoulder adduction. Wand run: a loose fist. Axes run: the second axe's head trails back and down outside the left thigh. First measure the hand's smallest distance from the pelvis midline over the cycle (solver 1's `solver_atk/runhand.py`). Legs byte-identical, sprints follow.
6. **chain_strike (arts.py), two hands (the owner, and the judge agrees):**
   - The judge's scale: at the 0.6 zoom she is about 3.6 px/cm, so a 7 mm gap is 2-3 px and reads closed, while 29 mm is about 10 px and shows. Measure the left fist's gap to the haft per frame, in screen plane and depth at the 0.6/315 camera.
   - Key the left hand onto the haft from the wind-up, as solver 2 suggested, and blend it off only on frames over about 8 mm.
   - The impact must read. The head lands edge-first and stays planted (it now rests as if set down). The haft is steeper, about 50 deg off the ground, with the right shoulder over the axe. She settles 3-5 cm lower over f6-f9 so the hold isn't frozen. The free arm stays back and out through f9 if it's free (it now drops limp to her knee by f9).

## Acceptance
- audit: no new flags on the changed clips.
- armscheck: the axe sets with the reaver outfit, and the wand with the arcanist outfit. Measure the stance clips with their own legs AND over idle_reaver/run_reaver legs (solver 1's `comp.py` makes play-true copies). No row deeper than before.
- fistfit: axe 21/21, wand 3/3.
- motion.py --outfits: no new arm-through-body contacts; slide not worse.
- Shoot to `tools/scratch/anim40/shots_atk3/`:
  - the shots_j1 lines, standing (the stance now shows);
  - axe_fore f0/f7, axe_heavy f7 and cast_flick f4 over `--hold-base run_reaver@0.3` (arcanist: `run_arcanist_wand@0.17`);
  - the three runs.
  Make a contact sheet. Don't judge beyond a working look.

## Return (under 40 lines)
What changed per clip, the numbers before and after, the commits, the shot folder, and what's still open with why.
