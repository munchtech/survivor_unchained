# Judge: her face's lighting in the close cinematic shots (cinematics 3, round 3, the last), effort max

Context budget: 150k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). The heroine's face is what players see most in the cinematics. Return a written verdict only; edit nothing. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (frames under godot/.shots/). Read only the files named here; open each image once. Keep the verdict under 50 lines. This is round 3, the last: for each FAIL say "must fix" (clearly wrong at 1:1, with the exact change) or "close as known".

## Finish line (the owner's rules)
A judge rules at the cameras the player has, at full size and critically: it must look perfect there. Marks seen only beyond that (enlarged crops, past the game's own zoom) are closed, not fixed. Judge only these 1:1 frames (1920x1080, the cinematic's own camera). "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore." Her materials (skin, eyes, hair) passed their own judges; judge only what the cinematic's lighting and framing do to her.

## Round 2 verdict and what changed ("rig" lights are soft spots on the characters' layer only, lasting the shot)
1. C01 s8 (frontal close-up by the coals): the eye light flattened her (shadow-side cheek L 35 -> 76, contrast 3.1:1 -> 2.0:1) and added no catchlight the ember didn't already give. Changed: the eye light is OFF in s8 (s8b, A5, A7 passed and keep theirs). Frames: k9c01_c01_s8_3.png; the reference with the right shadow side: k2c01_c01_s8_3.png. Has the shadow side and the ember warmth come back?
2. C01 s7 crown rim (over her shoulder, frost behind): no edge showed, and #b9c9ff matched the frost. Changed to your numbers: #ffd9b0, 2.0, 25 deg, from 0.30 m above and 0.15 m ahead of her eyes, aimed at the top-back of her head. Frame: k9c01_c01_s7_3.png. A warm band along the crown's top edge, hair not a helmet?
3. C02 s8 (the warden's lamp, night; note: "the flame small in each eye, the wet hair, the green weed the light finds and holds on ... Blue on one side of her face, her ember's red faint on the other"). Round 2: the light was on her left (the place offsets are world metres and the x sign was flipped), blown out, no flame in the eyes, the black band of his lamp-iron, too tight. Changed: the lamp light on her right (the lamp's side) at eye height, 0.28 m toward the lens, 0.25, #a8d2ff, specular 1.0; an ember light on her left, 0.15, #ff6a33, range 0.3 m; the warden hidden for this shot (no iron in frame); 90 mm, her eyes lowered toward the upper third. Frames: k9c02_c02_s8_1..3.png (round 2: k8c02_c02_s8_2.png). Also glance at k9c02_c02_s9_1.png: the warden must be back in frame there.
4. The neck seam fix landed (the outfits area; a stair-stepped pale patch and a white shard at her neck in round 2). Check her neck in k9c01_c01_s8_3.png, k9c01_c01_s8b_3.png, k9c03_c04a_sa5_1..3.png. Also confirm the eye light still reads in s8b (k9c01_c01_s8b_3.png) and A5.

## Verdict format
Items 1-4: PASS or FAIL, one or two lines why; for a FAIL, "must fix" with the exact change (energy, colour, world offset from her eyes bone in metres with which way she faces, cone, range), or "close as known". Then any NEW problem clearly visible at 1:1 that the cinematic's light or framing causes (only those).
