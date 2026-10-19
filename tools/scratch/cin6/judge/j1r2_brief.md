# Judge: cinematics C01-C04 fixes (cinematics 3, round 2), effort xhigh

Context budget: 180k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). Return a written verdict only; edit nothing. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (all paths below are inside it). Read only the files named here; open each image once. Keep the verdict under 60 lines. This is round 2 of at most 3: say plainly when an item is good enough to close.

## Finish line (the owner's rules)
A judge rules at the cameras the player has, at full size and critically: it must look perfect there. Marks seen only beyond that (enlarged crops, past the game's own zoom) are closed, not fixed. Judge only the 1:1 frames at the cinematic's own camera (1920x1080 PNGs; the contact sheets are only for continuity across a hand-over). "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore."

## The owner's words
- 17 Oct: "we go straight from the warden cinematic into a 3 second cross the river playtime into another cinematic. that will make players lose interest - have defeating the warden and the stuff stolen by grim also end with the ember going back into the ground cinematic".
- 18 Oct: "the silly slide across the log at the end of the first cinematic, and some polish issues. a couple overly long pauses that end up making animations look silly - some pauses are for narrative reasons thats great but if they go too long it gives people time to critique."
- 5 Oct, hand-overs: "cinematics that have our character immediately playable in the same spot should have us... in that same spot when we are playable again ... it should feel like its walking in and we just jump right into that."

Shot notes: godot/data/cinematics/c01.json, c02.json, c03.json, c04a.json, c04b.json (grep `"id": "<shot>"` and read only that shot's block).

## Excluded (other owners; don't mark)
- Her face's lighting (a separate judge).
- The stair-stepped pale patch / white shard on her neck in C01 s8, s8b, s10: the body's head-neck join, being fixed by the outfits area; those shots are re-shot after.
- Firelight specular spots on the Warden outfit's breast cups in C01 s10: logged for the outfits area.

## Round 1 marks and what was changed (frames under godot/.shots/, prefix k8)
- (b) C01 end. R1: s11 opened upright with the left hand at her chest, the sword popped into her hand, ~1 s frozen hold, blade tip into the log; s12 had no head / lost her. Changed: the pick-up clip starts at 0.45 s (cut lands mid-bend), @idle at 1.0 s, s11 dur 2.8 -> 2.2; s12's aim tracks her chest +0.2 m, and the camera now follows her own body after the hand-over (it read a hidden stand-in before). Frames: k8c01_c01_s11_1..6.png, k8c01_c01_s12_1..6.png; hand-over sheet godot/.shots/j1k8/c01_handover.jpg (every 0.2 s), at 1:1 k8c01_ho_c01_040_1.png. Check: no slide, no freeze, sword reaches her hand believably, tip clear of the log, her head in frame through s12, the hand-over lands her where she stood.
- (g) Crops from her 3 cm lower head. Changed: A3 aim +0.12, A5 -0.04, A7 -0.05, C01 s10 +0.03. Frames: k8c03_c04a_sa3_1..3, sa5_1..3, sa7_1..3, k8c01_c01_s10_1.png, _2.png.
- R1 new marks on C03: s10 was too tight and low (now eye height, pulled back 0.5 m); s11 had Grimtunnel's head out of frame (aim up 0.4 m). Frames: k8c03_c03_s10_1..3, s11_1..3, s12_1..3.
- (2) C03 s9 recoil. R1: late, limp; blade at his belly, tip on the warden's shoulder plate. Changed: a flinch, then at 0.12 s a guard pose (Idle_Shield_Loop for the Warden outfit), breathing on top. Frames: k8c03_c03_s9_1..3 (and s10-s12 above for how the guard holds). Tip 10 cm+ off the warden?
- (5) Frost seen from the play camera. R1: a grid of straight dark tile lines. Changed: tile boxes overlap 0.3 m and cross-fade. Frames: k8c01_ho_c01_036_1.png, _040_1.png, k8c01_c01_s12_4..6. If it still shows a grid, say so; the fallback is one decal for the whole patch.
- (a) C03 into C04 A (passed in R1; C03 s10/s11 were reframed since): one look at godot/.shots/j1k8/c03_c04a_cut.jpg and j1k8/c04a_handback.jpg.
- (4) Pacing, every Prologue cinematic. Numbers: tools/scratch/cin6/pace_k8.txt (per shot: start, length, last cue event, the quiet "tail" after it, camera move, her motion in cm between stills, voice lines). C02 and C04 B have no frames this round; rule on the numbers and the notes. Already trimmed: c01 6a 2.0; c02 s2 3.0, s3 3.0, s10 2.0; c03 s2 3.3; c04a A2 2.4 (R1 asked 2.2), A3 2.6, A7 tail 1.5; c04b B4a 2.2; c01 8b has a slow 0.05 m push. Rule: a tail over about 1 s where nothing moves is cut to 0.6-1.0 s; narrative pauses capped near 1.5 s; a camera move or a body moving counts as something happening. Give an exact list "cine shot: old dur -> new dur" for every shot still too long (or "none"), and flag any trim that cut a narrative pause too short. The last shot of a cinematic that blends into play (tagged "follow") is not a hold.

## Verdict format
For (b), (g), C03 s10/s11, (2), (5), (a), (4): PASS or FAIL, one or two lines why; for a FAIL the exact fix (shot, camera offset/aim/lens in metres, cue time, duration). Then any NEW problem clearly visible at 1:1 in these frames (not the excluded ones).
