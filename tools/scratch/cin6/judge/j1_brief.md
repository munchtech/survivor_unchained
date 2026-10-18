# Judge: cinematics C01-C04 fixes (cinematics 2, round 1), effort xhigh

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). Return a written verdict only; edit nothing. Read only the files named here (open each image once). Keep the verdict under 70 lines.

## Finish line (the owner's rules)
A judge rules at the cameras the player has, at full size and critically: it must look perfect there. Marks seen only beyond that (enlarged crops, past the game's own zoom) are closed, not fixed. Judge only the 1:1 frames at the cinematic's own camera (the PNGs are 1920x1080 game frames; the contact sheets are only for continuity across a hand-over). "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore."

## The owner's words
- 17 Oct: "we go straight from the warden cinematic into a 3 second cross the river playtime into another cinematic. that will make players lose interest - have defeating the warden and the stuff stolen by grim also end with the ember going back into the ground cinematic we get from crossing the river".
- 18 Oct: "the silly slide across the log at the end of the first cinematic, and some polish issues. a couple overly long pauses that end up making animations look silly - some pauses are for narrative reasons thats great but if they go too long it gives people time to critique."
- 5 Oct, hand-overs: "cinematics that have our character immediately playable in the same spot should have us... in that same spot when we are playable again ... it should feel like its walking in and we just jump right into that."

Shot notes are in godot/data/cinematics/c01.json, c03.json, c04a.json (each shot's "note"); read only the shots named below (grep for `"id": "<shot>"`).

## Frames (all under godot/.shots/)
- (a) C03 runs straight into C04 A (no wading in play between them): c03 shots k4c03_c03_s10_*.png, s11, s12 (3 stills each), then C04 A: k4c03_c04a_sa1_*.png, sa2. Continuity sheet of the cut: j1/c03_c04a_cut.jpg (hand-over frames in time order). C04 A's hand-back into play: j1/c04a_handback.jpg, and at 1:1 k4c03_ho_c04a_078_1.png, k4c03_ho_c04a_080_1.png.
- (b) C01's end, the slide removed: shot 11 now cuts onto her picking up (no glide along the log), shot 12 is re-aimed at her chest (her head was out of frame): k4c01_c01_s10_*.png, s11, s12 (6 stills each). Hand-over into play: j1/c01_handover.jpg; at 1:1 k4c01_ho_c01_040_1.png.
- (d) An ember drifting across the lens made an orange disc on her cheek at C01 s10 (now kept clear of close lenses): check k4c01_c01_s10_*.png.
- (g) Her head is 3 cm lower on the new body: check every close framing for crops (top of head, eyes against the letterbox bars, chin): k4c01_c01_s7_3.png, s8_3, s8b_3, s12_3; k4c03_c03_s3_2.png, s3b_2, s7_2, s8_2, s10_2; k4c03_c04a_sa3_2.png, sa4_2, sa5_2, sa6_2, sa7_2.
- (2) C03 s9: Grimtunnel bursts up and snatches the heart from under her raised hand. Before, she held the reach frozen through s9-s12 (22 s); now she flinches and pulls the hand back into a breathing stance: k4c03_c03_s9_1.png, _2, _3, and s10-s12 above. Does the recoil read natural?
- (5) Frost after C01, seen from the play camera: the frost patch was a 44 m square with straight edges, and its tiles' boxes stopped short on slopes (straight seams). Now a round ragged edge and boxes that span each tile's slope: k4c01_ho_c01_036_1.png, _040_1.png (play camera). Any straight lines or square seams in the frost?
- (4) Pacing: tools/scratch/cin6/pace_k4.txt (each shot: start, length, last event, the quiet "tail" after it, camera move, her motion in cm between stills, lines). Trims made: c01 6a 3.0->2.4; c02 s2 4.0->3.0, s3 3.5->3.0, s10 2.5->2.0; c03 s2 4.0->3.3; c04a A2 5.0->4.0, A3 3.5->2.6, A7 tail 3.0->1.5; c04b B4a 2.6->2.2. Rule used: a tail over ~1 s where nothing moves is cut to 0.6-1.0 s; narrative pauses ("a beat", "hold") capped near 1.5 s. Flag any remaining hold that outlasts its beat, or a trim that cuts a narrative pause too short. (Her motion of 0.0 cm in c01 s7-s9 is a measuring artefact: a new procedural breath runs there but the log reads the pose before it.)

## Checklist and verdict format
For each of (a), (b), (d), (g), (2), (5), (4): PASS or FAIL, one or two lines why, and for a FAIL the exact fix (which shot, what to change: camera offset/aim/lens in metres, a cue time, a duration). Then list any NEW problem that is clearly visible at 1:1 in these frames (only those; nothing from enlarging). Don't judge her face's lighting (a separate judge does).
