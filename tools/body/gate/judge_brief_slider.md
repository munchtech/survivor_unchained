# Judge brief: P1 gate again (slider route), her bare body, A (shipped) vs the NEW B (ours, from our sliders), at the game's cameras (max)

Item: P1 gate slider

You are a fresh judge (Survivor Unchained, a dark-fantasy 18+ action game; she is the heroine, always on screen). Read-only: look, decide, write the verdict. You may crop or zoom the pictures with a short Python/Pillow script to see them at 1:1 (the files are 3840x1080: A is the left 1920, B the right 1920); no measuring, no edits to anything in the repo. One pass, no fix rounds.

The owner's bar: "would this frame ship in a AAA game as it stands?" Rule at the cameras the player has (play/town camera, the close-up camera, character creation's Look camera), at full size and critically. Marks seen only beyond that are logged, not fixed.

## What changed since the last gate (which picked A)
The last B was A's sculpt COPIED onto our base (a per-vertex residual); it brought a left-deltoid knob, shrugged high wide shoulders, a hard throat seam, a pinker torso. The owner then chose: "a perfect copy is not needed if it makes a better pipeline going forward". The NEW B is shaped by OUR sliders alone (set by design, no copy of A): shoulders in, hourglass waist and hips, full high breasts (our own designed lift target), a full round butt (our own designed lift target), athletic limbs. Its skin paint is A's, carried on our UVs. Her throat under the head's seam now takes the same skin treatment as A's neck. So B is meant to be a different, designed body, not A's twin: judge it as her body, against A's quality.

The owner's priorities on her shape: "perfect breasts, not exactly a perfect copy, but very well done"; "breast and butt are very important as sex appeal is a big deal"; busty, athletic, sex appeal driving but never looking bad; shoulders not shrugged.

## What you see
Four A|B pairs, same head, same cameras, bare (no outfit), in `C:\Users\munch\Desktop\survivorsunchained_inputs\body_p1\slider\`:
- `GATE_look_look_1to1.png`: character creation's Look camera (the closest the player sees her body).
- `GATE_close_town_1to1.png`: the close-up camera, town idle.
- `GATE_play_town_1to1.png`: the play camera in town (far; she is ~100 px tall).
- `GATE_play_play_1to1.png`: the play camera in the arena, idle.
A = the body shipped today. B = our own rebuilt body. The arm band on A is a paint layer not yet mapped to B; ignore that difference. The sheet with captions: `GATE_sheet_half.jpg` there.

Supplementary (bend strips of the new B, bare clay, close tier, panels 0/90/135): `STRIPS_DIR\strip_shoulder_flex.png` and `strip_hip_flex.png`.

## Known, named (do not re-litigate, but say if it is worse than described)
- **Hip 112/135 is OPEN** (a named known; a soft-tissue route is planned after the pick): at 135 a hard dark line where the thigh meets the belly. Not part of this verdict's pass or fail.
- The idle hand pose and the arm band are not body-shape items (log only).

## Questions, in order
1. For each pair, the whole-frame question first, for B and for A: would it ship in AAA as it stands? (YES / NO, one reason.)
2. For each pair, A vs B: which is better, and the one thing that decides it.
3. Her breasts and her butt on B, at the Look and close-up cameras: very well done or not, and the one change that would most improve each (in slider terms if you can: higher, rounder, fuller, closer, a softer underbust fold, more projection...).
4. Last gate's B defects, each: gone, better, same or worse: the left-deltoid knob, shrugged/wide shoulders, the throat seam, the torso pinker than the head, waxy skin.
5. New B defects you see at 1:1 (where, how big, how often seen).
6. Your recommendation to the owner: A or B for the bare shape, in one line, with the one fix that matters most if B.

## Output (write it to the --out file, plain markdown, short)
- `SHEET:` four lines, one per pair, each under 160 characters: `<pair>: A <YES/NO>, B <YES/NO>; <A or B> better: <reason>`.
- `HANDOFF:` two lines: the overall verdict (A or B, the one fix), and one line on her breasts and butt.
- Then your detail for questions 3-6 (at most 18 lines).
