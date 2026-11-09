# Judge brief: P1 gate, her bare body, A (shipped) vs B (ours), at the game's cameras (max)

Item: P1 gate

You are a fresh judge (Survivor Unchained, a dark-fantasy 18+ action game; she is the heroine, always on screen). Read-only: look, decide, write the verdict. You may crop or zoom the pictures with a short Python/Pillow script to see them at 1:1 (the files are 3840x1080: A is the left 1920, B the right 1920); no measuring, no edits to anything in the repo. One pass, no fix rounds.

The owner's bar: "would this frame ship in a AAA game as it stands?" A judge rules at the cameras the player has (play/town camera, the close-up camera, character creation's Look camera), at full size and critically. Marks seen only beyond that are logged, not fixed.

## What you see
Four A|B pairs, same head, same cameras, bare (no outfit), in `C:\Users\munch\Desktop\survivorsunchained_inputs\body_p1\`:
- `GATE_look_look_1to1.png`: character creation's Look camera (the closest the player sees her body).
- `GATE_close_town_1to1.png`: the close-up camera, town idle.
- `GATE_play_town_1to1.png`: the play camera in town (far; she is ~100 px tall).
- `GATE_play_play_1to1.png`: the play camera in the arena, idle.
A = the body shipped today (MakeHuman-derived). B = our own rebuilt body (our topology, skeleton, weights, correctives, UVs, bake). The arm band on A is a paint layer not yet mapped to B; ignore that difference.

Supplementary (bend strips of B, bare clay, close tier, panels 0/90/135): `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_body_p1\lead3\ek2\final\close\strip_shoulder_flex.png` and `strip_hip_flex.png`.

## Known, named (do not re-litigate, but say if it is worse than described)
- **Hip 112/135 is OPEN** (a named known; a soft-tissue route is planned after the pick): at 135 a hard dark straight line where the thigh meets the belly. It is not part of this verdict's pass or fail.
- At shoulder flex L 135 (the strip): ribcage streaks and a chest slash. Name them in one line: how bad, would they be seen in normal play.
- The lead's notes on B (check each, at 1:1): a lumpy bump at her left deltoid/armpit; shoulders higher and wider than A; breasts lower with a deep underbust fold; a bluish patch / faint line at the front of the throat.

## Questions, in order
1. For each pair, the whole-frame question first, for B and for A: would it ship in AAA as it stands? (YES / NO, one reason.)
2. For each pair, A vs B: which is better, and the one thing that decides it.
3. The B defects you see at 1:1 that the list above misses (where, how big, how often seen).
4. Your recommendation to the owner: A or B for the bare shape, in one line, with the one fix that matters most if B.

## Output (write it to the --out file, plain markdown, short)
- `SHEET:` four lines, one per pair, each under 160 characters: `<pair>: A <YES/NO>, B <YES/NO>; <A or B> better: <reason>`.
- `HANDOFF:` two lines: the overall verdict, and the shoulder-flex streaks/slash line.
- Then your detail for questions 3 and 4 (at most 15 lines).
