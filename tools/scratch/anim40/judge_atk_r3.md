# Judge brief: her attack poses and runs (animation 43, item 2, round 3 of 3: the LAST round)

Context budget: 180k. Read-only: your final message is the verdict. Don't write files or run scripts.

## The bar
The owner: "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore."
- A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there.
- Judge at 1:1 only. A mark that only shows enlarged is closed.
- These are her MAIN ATTACKS and her runs. They are seen all the time, so judge them at full detail.

**Whole-frame gate first** (the owner, 18 Oct: "that quality is nowhere near what we are supposed to be pushing for").
- For each frame, before any checklist, ask: *would this frame ship in a AAA game as it stands?* Answer as a player at 1:1, about the whole picture: anatomy and pose, face and hair, light, camera, staging. A NO fails the frame.
- Calibrate first on the owner's three failing frames in `C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\`:
  - a masculine throat under an upside-down camera;
  - a collapsed head-down hunch, a gray neck and a floating pauldron;
  - a hard pale hairline, a detached braid tab, waxy skin and a jarring spin.
- Tag what isn't animation's `[not-anim: area]`. It still counts against the gate. Two such marks are already routed and known:
  - the reaver's front loincloth panel sticking out in a crouch `[not-anim: outfit]`;
  - no contact shadow at the 0.6 zoom `[not-anim: light]`.

The owner on motion: "bad, unnatural movements with respect to wrists - follow through motion joint to joint, some elbow pinching or arms going through body or breast, some sliding."

Round 2's verdict is in `judge_atk_r2_verdict.md` (same folder as this brief). Read it first: it has what failed and the fixes asked for.

## What changed since round 2
- **axe_fore, axe_heavy, axes_left, axes_right (folder shots_atk5):**
  - The left hand is off her hip: at f7 it is 24 cm out and 12 cm behind, with the elbow at 107 deg.
  - The finish is committed: the trunk leans 15 deg (was 4.5) and rolls to her left, the right elbow is at 151 (was locked at 176), and the fist is 35 cm in front of her.
  - The run-layer finishes clear her forward knee by 9-15 cm over the whole cycle.
  - Heavy is apart from fore: at f0 the haft is laid back and the head sits behind her shoulders, 25 cm lower; heavy is keyed with more spine pitch.
  - heavy7: the head rolled toward the camera (flat 0.20 -> 0.58, the wrist limit stopped it there).
  - Fore f0: the elbow is up and back, and her face is 8 cm clearer.
  - Dual axes: the guard haft is 5-12 cm further from her face, and the idle axe at axes_right f7 is tipped back behind her shoulder.
  - These shots have a different town backdrop and light from round 2. Don't judge the backdrop.
- **chain_strike (shots_atk5b), restaged:**
  - f0-f1: she lands standing, both hands on the haft overhead, the axe head behind her head.
  - f2: the chop comes over.
  - f3-f9: a crouch, knees out over the toes, the torso at about 45 deg (was horizontal), her head above her shoulder line, the arms long down the haft.
  - Hips never drop before f3, and no knee or hand touches the ground.
  - Known: at f0-f1 the left fist sits 11-19 mm off the haft.
- **cast_flick (shots_atk5b):**
  - She now has a real stance (feet 48 cm apart, knees about 15 deg).
  - At f8 the wand reaches nearly straight ahead, 11 deg below level, with the free hand by her hip.
  - At f0 the wand tip goes back over her right shoulder.
- **The runs (shots_atk6; ignore the wrun/axrun in shots_atk5b, they are stale):**
  - The free left arm is further out from her side, its forward extreme 25-28 cm from her midline. run_reaver, which passed round 1, sits at 26.
  - The wand run's free hand is a fist.
  - **Known open in the axes run:** the second axe's head points forward and down while that forearm swings forward. The solver says it can read as hanging across her front toward her groin from the 315 camera. Rule on whether it does at 1:1. If it fails, say whether carrying it hanging at her side (elbow about 150 deg, head beside her shin, outside the knee) is the right restage.

## Frames (1920x1080, the real game, day)
All folders are under `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\scratch\anim40\`.

Open these 34 PNGs, and only these:
- **shots_atk5/:**
  - fore0_m, fore3_m, fore7_m
  - heavy0_m, heavy4_m, heavy7_m
  - axesl3_m, axesr3_m, axesr7_m
  - fore3_f45_m, heavy4_f45_m
  - fore0_run_m, fore7_run_m, heavy7_run_m
- **shots_atk5b/:**
  - chain0_m, chain2_m, chain3_m, chain6_m, chain9_m, chain3_p
  - flick0_m, flick1_m, flick4_c, flick8_m, flick4_run_c
- **shots_atk6/:**
  - wrun_c, wrun_m, wrun_p
  - axrun_c, axrun_m, axrun_p

Each folder's list (`shots_atk5.txt`, `shots_atk5b.txt`; atk6 uses atk5b's run lines plus the `_m` zoom) gives each frame's clip and time. 30 fps, so @0.1 = f3.

Suffixes:
- `_m`: the close-up at zoom 0.6.
- `_c`: the close-up at its closest zoom.
- `_p`: the play camera.
- `_run_`: the swing over her run's legs, the most common case in play.

Mid-swing frames (fore f3, heavy f4, axes f3, chain f2, flick f1) are on screen for about 20 ms. Judge those for a broken or ugly pose only.

## Checklist (after the gate)
1. Pose: strong, athletic, intentional. The stance carries her weight. No hunch, no collapsed head.
2. The weapon reads, held, with its line right for the moment. It doesn't drag, rest on her leg or pass through her at 1:1.
3. The free hand is purposeful. It is never at her groin or belly, clamped on her hip or behind her back, and there are no T-pose or A-pose arms. In chain_strike, both hands read on the haft.
4. Wrists and elbows: no broken, wrung or pinched joint. No arm through her breast or trunk.
5. Heavy reads heavier than fore (f0, f7, f7_run).
6. The wand never goes through the hat.
7. Runs: the free hand's swing reads natural and off her midline, and the gait is unchanged.

## Return (under 60 lines)
1. Per frame: GATE yes/no (one line), then PASS/FAIL with tagged marks.
2. Then, since this is the LAST round, for each failing frame, one of three calls:
   - (a) a small fix a solver can make in one pass, made concrete (clip, frame, which hand, which way, roughly how much);
   - (b) RESTAGE, with what the restage should be;
   - (c) the frame passes the gate, and the mark is small enough to close as known.

Ask for any measurement you need. Don't open crops.
