# Judge: cinematics C01-C04 fixes (cinematics 3, round 3, the last), effort xhigh

Context budget: 180k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). Return a written verdict only; edit nothing. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (all paths below are inside it). Read only the files named here; open each image once. Keep the verdict under 60 lines. This is round 3, the last: an item that still fails closes as known unless the miss is plainly visible and cheap to fix, so say for each FAIL whether it is "must fix" (clearly wrong at 1:1) or "close as known".

## Finish line (the owner's rules)
A judge rules at the cameras the player has, at full size and critically: it must look perfect there. Marks seen only beyond that (enlarged crops, past the game's own zoom) are closed, not fixed. Judge only the 1:1 frames at the cinematic's own camera (1920x1080 PNGs; the contact sheets are only for continuity across a hand-over). "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore."

## The owner's words
- 17 Oct: "we go straight from the warden cinematic into a 3 second cross the river playtime into another cinematic. that will make players lose interest - have defeating the warden and the stuff stolen by grim also end with the ember going back into the ground cinematic".
- 18 Oct: "the silly slide across the log at the end of the first cinematic, and some polish issues. a couple overly long pauses that end up making animations look silly - some pauses are for narrative reasons thats great but if they go too long it gives people time to critique."
- 5 Oct, hand-overs: "cinematics that have our character immediately playable in the same spot should have us... in that same spot when we are playable again ... it should feel like its walking in and we just jump right into that."

Shot notes: godot/data/cinematics/c01.json, c02.json, c03.json, c04a.json, c04b.json (grep `"id": "<shot>"` and read only that shot's block).

## Excluded (other owners; don't mark)
- Her face's lighting (a separate judge).
- Firelight specular spots on the Warden outfit's breast cups in C01 s10: logged for the outfits area.

## Round 2 marks and what was changed (frames under godot/.shots/, prefix k9)
- (b) C01 s11. R2: still 1 upright, the sword popped in, stills 2-3 frozen, the tip on the log, the log's sword still there while hers was in her hand. Changed: her own `take_from_log` clip (the right hand closes on the grip, she turns about 110 deg to her left) from 0.5 s; the log's sword and shield leave and hers is in her hand on the cut; she turns toward r1 over 0.3-1.3 s; dur 1.8. Blade tip measured at least 0.35 m above the log. Frames: k9c01_c01_s11_1..6.png.
- (b) C01 s12, the crane into play. R2: still 1 cut her above the lips, still 2 lost her, still 3 a sliver. Changed: the camera's look during the blend into the game camera now aims from where the crane is (a code fix), the crane starts 3.9 m from her chest. Frames: k9c01_c01_s12_1..6.png; the hand-over sheet godot/.shots/j1k9/c01_handover.jpg, at 1:1 k9c01_ho_c01_040_1.png.
- (g) C04 A A7: eyes too high (19% from the top). Changed: aim -0.05 -> -0.03. Frames: k9c03_c04a_sa7_1..3.png.
- C03 s9-s11 (s9 note: "Grimtunnel, up to the waist, snatches the heart out of the air and hugs it to his chest"; s10: "From her eye height, down at him: in his arms the heart's light goes on straining out toward her. He looks down at it, up at her..."; s11: "G3, broken in the middle, half over his shoulder; he dives head first, still clutching the heart"). R2: the heart never held, its light blew out his torso, he stood at full height in shin-deep water, her blade tip on the warden's hood, s10 cut his head off, s11 cut her eyes off. Changed: he is sunk 0.55 m (waist-deep), holds the heart in his arms (a new hug pose), the heart's glow 0.15; she is turned so her blade clears the warden; at that height his hat brim hid his face from any camera at her eye height, so the cameras come down to his eye line (a low cheat on "down at him"); in s11 he has turned away to dive and speaks back over his shoulder. Frames: k9c03_c03_s9_1..3, s10_1..3, s11_1..3, s12_1..3.
- C01 s10 re-shot after the outfits area's neck seam fix (a stair-stepped pale patch below her ear in round 1): k9c01_c01_s10_1..6.png. Is her neck clean at 1:1?
- (4) Pacing, applied from your round-2 list: c01 s6 6.4, s11 1.8; c02 s2 2.4; c03 3b 1.9; c04a A2 2.2; c04b B4a 1.7, B4b 1.7. Nothing to judge unless a frame shows a cut too early; one line.
- (a) C03 into C04 A in REAL PLAY (round 2 judged the shot version; this run is the game itself: a quick start played by the autopilot with every cinematic on, the Warden killed in the fight, C03 on his death, C04 A on the cut, then play). Frames every 10 s plus one still per cinematic shot: godot/.shots/playc2_*.png; the log tools/scratch/cin6/logs/playc2.log (grep `cinema:` for when each starts and ends, and `saved` for which frame is when). Check only the frames from the last C04 A shot to two frames after `cinema: c04a done`: is she where C04 A left her, is the game camera on her, does play carry on (the autopilot walks her up the road)?

## Verdict format
For each item: PASS or FAIL, one or two lines why; for a FAIL, "must fix" or "close as known", and for "must fix" the exact change. Then any NEW problem clearly visible at 1:1 in these frames (not the excluded ones), only if it is plainly wrong.
