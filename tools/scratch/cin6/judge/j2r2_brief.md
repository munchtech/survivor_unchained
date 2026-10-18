# Judge: her face's lighting in the close cinematic shots (cinematics 3, round 2), effort max

Context budget: 150k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). The heroine's face is what players see most in the cinematics. Return a written verdict only; edit nothing. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (frames under godot/.shots/). Read only the files named here; open each image once. Keep the verdict under 50 lines. This is round 2 of at most 3: say plainly when an item is good enough to close.

## Finish line (the owner's rules)
A judge rules at the cameras the player has, at full size and critically: it must look perfect there. Marks seen only beyond that (enlarged crops, past the game's own zoom) are closed, not fixed. Judge only these 1:1 frames (1920x1080, the cinematic's own camera). "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore." Her materials (skin, eyes, hair) passed their own judges; judge only what the cinematic's lighting and framing do to her.

## Excluded
The stair-stepped pale patch and white shard on her neck in C01 s8/s8b: the body's head-neck join (not lighting; it stays with every shadow off), being fixed by the outfits area. Don't mark it.

## Round 1 verdict and what changed ("rig" lights are soft spots on the characters' layer only, lasting the shot)
1. Eye light (0.3, #fff3e6, just above the lens). R1: alive at s8b and A7, but at C01 s8 it flattened her (the shadow side lit up, the ember warmth gone); A5 couldn't be judged (eyes shut). Changed: cone narrowed 14 -> 5 deg, aimed between her eyes. Frames: C01 s8 k8c01_c01_s8_3.png (reference with the shadow side, before any eye light: k2c01_c01_s8_3.png); C01 s8b k8c01_c01_s8b_3.png; C04 A5 k8c03_c04a_sa5_1.png, _2, _3 (judge the frames where her eyes are open; say if none are); A7 k8c03_c04a_sa7_1.png, _3. Do her eyes read alive, does s8 keep its shadow side, any hotspot or wrong catchlight?
2. Crown rim, C01 s7 (over her shoulder). R1: no rim showed (the light was on the camera's side). Changed: moved to the far side of her head, 1.5, #b9c9ff. Frame: k8c01_c01_s7_3.png. Does the crown now read as hair with an edge, not a flat "helmet" dome?
3. C02 s8 (her face in the warden's held lamp, night; the note: "Her face in the lamp's light: the flame small in each eye, the wet hair, the green weed the light finds and holds on. Close enough to her lips that breath would show; none does. Blue on one side of her face, her ember's red faint on the other."). R1: lamp at 1.0 still bleached the near hair and greyed her skin; no flame in the eyes; dark crescents under the eyes; the lamp-iron shaft made a black band; hot white patches on her shoulder guards. Changed: frontal 100 mm framing; the lamp light moved to her eye height, 0.20 m to her right, 0.28 m toward the camera, 0.8, #a8d2ff, range ending at her jaw. Frames: k8c02_c02_s8_1.png, _2, _3 (R1's frontal for comparison: k6front_c02_s8_2.png). Is the flame small in her eyes, blue one side, a faint ember red the other, hair brown not cream, no black band, no shoulder hotspots? If her left cheek has no ember red, say how much to add (an ember light there at about 0.15 was proposed).

## Verdict format
Items 1-3: PASS or FAIL, one or two lines why; for a FAIL the exact change (energy, colour, offset from her eyes bone in metres [x = her left, y up, z out of her face], cone angle, range). Then any NEW problem clearly visible at 1:1 that the cinematic's light or framing causes (only those).
