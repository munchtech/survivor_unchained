# Judge: her face's lighting in the close cinematic shots (cinematics 2, round 1), effort max

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). The heroine's face is what players see most in the cinematics. Return a written verdict only; edit nothing. Read only the files named here (open each image once). Keep the verdict under 60 lines.

## Finish line (the owner's rules)
A judge rules at the cameras the player has, at full size and critically: it must look perfect there. Marks seen only beyond that (enlarged crops, past the game's own zoom) are closed, not fixed. Judge only these 1:1 frames (1920x1080, the cinematic's own camera). "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore." Her materials (skin, eyes, hair) passed their own judges; here judge only what the cinematic's lighting and framing do to her.

## What changed (a "rig" cue: a soft spot light on the characters' layer only, lasting its shot)
1. Dead eyes at C01 s8/s8b and C04 A5/A7: an eye light of 0.3 (#fff3e6, from just above the lens), like the game's close-up camera's key.
2. C02 s8: the warden's held lamp bleached her braid and greyed her skin at 2.0 (#8ac8ff); now 1.0, #a8d2ff.
3. C01 s8: a warm fill (0.25, #ffc890) under her left eye.
4. C01 s7: a rim light on her crown (0.8, #b9c9ff, from above and behind), against a flat "helmet" dome of hair.
5. C02 s8: a hard dark vertical band down the frame's left edge. It is the warden's lamp-iron shaft (he holds the lamp beside her face), in focus. Three framings were tried; pick one direction.

## Frames, before then after (godot/.shots/)
- C01 s7 (over her shoulder, the crown rim): before k1c01_c01_s7_3.png, after k4c01_c01_s7_3.png.
- C01 s8 (frontal CU, eye light + warm under-eye fill): before k2c01_c01_s8_3.png, after k4c01_c01_s8_3.png.
- C01 s8b (tighter CU, eye light): before k2c01_c01_s8b_3.png, after k4c01_c01_s8b_3.png.
- C04 A A5 (frontal CU at dawn, eye light): before k2c04a_c04a_sa5_2.png, after k4c03_c04a_sa5_2.png.
- C04 A A7 (frontal CU, a slow push, eye light): before k2c04a_c04a_sa7_2.png, after k4c03_c04a_sa7_2.png.
- C02 s8 (her face in the warden's lamp light, night; the note: "Her face in the lamp's light: the flame small in each eye, the wet hair, the green weed the light finds and holds on. Close enough to her lips that breath would show; none does. Blue on one side of her face, her ember's red faint on the other."): before (lamp 2.0) k2c02_c02_s8_2.png; lamp 1.0, 135 mm from her right three-quarter (the band at left; her lips out of frame) k4c02_c02_s8_2.png; frontal 100 mm k6front_c02_s8_2.png; left three-quarter 100 mm k6c02_c02_s8_2.png.

## Checklist and verdict format
For items 1-4: PASS or FAIL, one or two lines, and for a FAIL the exact change (energy, colour, the light's offset from the lens or her bone in metres, or the angle). Say whether the eyes now read alive, whether any rig light makes a visible hotspot, a second catchlight that looks wrong, or flattens her. For item 5: which framing (or a fourth: give pos offset [x, y, z] from her eyes bone in metres, aim offset, lens mm), whether lamp 1.0 still bleaches her skin or hair, and what to change. Then any NEW problem clearly visible at 1:1 in these frames that the cinematic's light or framing causes (only those).
