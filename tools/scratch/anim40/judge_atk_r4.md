# Judge brief: her attack poses and runs (animation 44, item 2, round 4: the restage round, the LAST)

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

Round 3's verdict is in `judge_atk_r3_verdict.md` (same folder as this brief). Read it first: it has what failed and the fixes asked for.


## The hard stop
This is the last round. Anything that fails the gate is CUT: it falls back to the clip it replaces, or it is gated off. So, for each failing frame, say whether the previous version (r3's frame, judged in the r3 verdict) would be the better fallback.

## What changed since round 3 (one restage round on the 16 failures; your calls 1-9 in the r3 verdict)
- **Calls 1-5, the axe swings (axe_fore, axe_heavy, axes_right, axes_left):**
  - The head roll at every f7 finish went from -25/-30 deg to within ±3. Heavy's chin is up.
  - heavy0: the back knee is at 35 deg and her legs are loaded. Open: the pelvis drops only 2 cm.
  - axesr7: the left axe holds the f3 shape (out to her left, edge forward).
  - fore0_run: the left arm is out from her body.
  - fore7_run and heavy7_run: the fist sits beside her left hip and the head trails outside the thigh.
  - The `_run` frames play new run variants (axe_fore_run, axe_heavy_run) while she moves.
  - **axesl7_m is new:** axes_left plays the changed keys mirrored. Judge it like axesr7.
- **Call 7, cast_flick:** the free arm hangs 6-7 deg from her side, elbow 100, hand clear of the hip. At f4-f8 the wand hand is at her chest, the elbow at 147, the shoulder forward. The wand sits 4 deg above level on purpose: from the 315 camera it reads about level.
- **Call 6, chain_strike: NOT changed.** The rig can't meet it: the wrist limit holds the haft at 33-35 deg, and the grip is fixed on the haft. chain3/6/9 below are r3's frames again. Rule: does each pass the gate as it stands? If not, the clip falls back to integration's earlier chain_strike, or is gated off.
- **Call 8, run_arcanist_wand:** the free fist's forward extreme is at lower-rib height (navel +14 cm, 1 cm under the underbust, 13 cm in front of the bust), elbow 85, 27 cm out. The back extreme is now 7.5 cm behind the hip (it never went behind her before).
- **Call 9, run_reaver_axes, restaged:** the second axe hangs at her side with the edge back. Elbow 146-152, upper arm 13-24 deg out. The haft trails 14-32 deg back of vertical (about 30 at the back of the swing). The head stays about 40 cm clear of her knee, shin and feet, and the fist stays behind her hip crease all cycle. The likely weak points: the left wrist sits near its ulnar limit (43 of 45 deg), and the haft swings about ±9 deg with the arm.

## Frames (1920x1080, the real game, day)
All folders are under `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\scratch\anim40\`.

Open these 21 PNGs, and only these:
- **shots_atk7/:**
  - heavy0_m, heavy7_m
  - axesr7_m, axesl7_m (new)
  - fore0_run_m, fore7_run_m, heavy7_run_m
  - flick4_c, flick8_m, flick4_run_c
  - wrun_c, wrun_m, axrun_c, axrun_m
  - Controls that passed r3 (confirm they still pass): fore7_m, flick0_m, flick1_m, wrun_p, axrun_p.
- **shots_atk5b/ (unchanged since r3):** chain3_m, chain6_m, chain9_m.

Frame lines (clip and time) are in `shots_atk5.txt` and `shots_atk5b.txt`. The `_m` runs use the run lines with zoom 0.6. 30 fps, so @0.1 = f3.

Suffixes:
- `_m`: the close-up at zoom 0.6.
- `_c`: the close-up at its closest zoom.
- `_p`: the play camera.
- `_run_`: the swing over her run's legs, the most common case in play.

## Checklist (after the gate)
1. Pose: strong, athletic, intentional. The stance carries her weight. No hunch, no collapsed head, no head rolled onto a shoulder.
2. The weapon reads, held, with its line right for the moment. It doesn't drag, rest on her leg or pass through her at 1:1.
3. The free hand is purposeful. It is never at her groin or belly, clamped on her hip or behind her back, and there are no T-pose or A-pose or T-rex arms.
4. Wrists and elbows: no broken, wrung or pinched joint. No arm through her breast or trunk.
5. Heavy reads heavier than fore.
6. The wand never goes through the hat.
7. Runs: the free hand's swing reads natural and off her midline, the second axe reads as carried (not a wing, not across her front), and the gait is unchanged.

## Return (under 50 lines)
1. Per frame: GATE yes/no (one line), then PASS/FAIL with tagged marks.
2. For each failing frame, one call:
   - CUT, with the fallback you'd ship: r3's version, integration's, or gated off;
   - or KNOWN: it passes the gate, and the mark is small enough to close.
3. For any CUT, the fix you'd give a later round, in one line.

Don't open crops.
