**Verdict: cinematics C01–C04 fixes (cinematics 2, round 1). Not finished: 2 of 7 items pass, 5 fail.**

**(a) C03 runs straight into C04 A: PASS.** In `c03_c04a_cut.jpg` the last C03 frames (ho_c03_010–015) cut straight to C04 A (ho_c04a_017+) with no play in between. She is at the ford in s12 and wading toward the bank in A1, so the geography holds. The hand-back (`c04a_handback.jpg`, ho_078/080) puts her on the road in the play camera, same spot every frame, and the title is clean.

**(b) C01 end, slide removed: FAIL.** The glide is gone: her feet stay put through s11_1–4. Three things are still wrong:
- **s11 opening pose.** She is upright and empty-handed with her left hand pressed to her chest, which reads as a grab at her breast, not "already bending to her weapon". The sword just appears in her hand by s11_2 (66 cm of movement in one interval).
- **s11 freeze.** She holds the sword level at her hip, frozen, for about 1 s (s11_2/3/4 are identical, 0.0 cm). At the end (s11_6) the blade tip sinks into the top of the log.
- **s12 re-aim did not land.** s12_1 still has no head: the top of the frame cuts at her shoulders and the centre of the frame is on her belt. In s12_2 she is out of frame (the crane looks down at the fire and bedroll). In s12_3 she is in the bottom-right corner, cut by the bar.
- **Fix s11:** start the pick-up clip about 0.3 s earlier so the cut lands mid-bend with her right hand going to the hilt. Start the "comes round ready" turn at about 0.7 s instead of about 1.7 s, or cut s11 from 2.8 to 2.0 s. Keep the blade tip 5 cm or more clear of the log.
- **Fix s12:** raise the aim about 0.45 m to her sternum/neck (about 1.45 m above the ground). Start the camera about 2.4 m in front at 1.6 m height so the frame runs head to mid-thigh with a little headroom. Keep the look-at locked on her for the whole up-and-round, and blend to the game camera's target only in the last 0.8 s.

**(d) Ember disc on her cheek: PASS.** No orange disc anywhere in s10_1–6; the cheek is clean in both close stills.

**(g) Crops from the 3 cm lower head: FAIL**, on two C04 A shots:
- **A3 (sa3_2), side-on medium shot.** The top of her head is cut by the top bar and her eye is only about 90 px below it. **Fix:** raise the aim 0.12 m, or pull the camera back 0.35 m.
- **A7 (sa7_2), frontal close-up, 13.9 s.** Her chin runs into the bottom bar and her eyes sit at mid-frame; the 0.05 m push makes it worse. **Fix:** lower the aim 0.05 m so the eyes sit at the upper third and the chin clears the bar at the end of the push.
- **A5 (sa5_2)** has the same problem, milder: chin about 40 px above the bar. **Fix:** lower the aim 0.04 m.
- **Fine:** c01 s7_3 (over the shoulder), s8_3 and s8b_3 (top of head cut, normal for a close-up; eyes and chin clear), c03 s3b_2 (good headroom), A6 (sa6_2). c03 s3_2, s7_2, s8_2 and s10_2 are not framings of her face. c01 s12_3 is covered under (b).
- **Minor:** in c01 s10_1/2 the top of her head just touches the bar. Lower the aim 0.03 m.

**(2) C03 s9 recoil: FAIL.** The 22 s frozen reach is gone, but in s9_1 Grimtunnel already has the heart and she is still holding the blade level at his belly, so it looks like she is skewering him. The 15 cm pull-back only happens between stills 1 and 2, so the flinch reads late. It then settles into a limp stance: sword hanging, tip resting on the warden's shoulder plate (s9_2/3) and near Grimtunnel's hand in s11_3. **Fix:** start the recoil 0.1–0.15 s after the burst and make it about 0.35 s long. End it in a low guard: sword hand at hip, blade angled about 30° up toward Grimtunnel, weight on the back foot, with the breathing on top. Keep the tip 10 cm or more off the warden.

**(5) Frost seen from the play camera: FAIL.** ho_036 and ho_040 show a regular grid of thin, straight dark lines across the frost: vertical near x≈1390 and x≈1880, horizontal near y≈300 and y≈620. The same grid shows in c01 s12_4–6. These are the tile borders. The round edge is off-frame in these views, so it isn't judged. **Fix:** grow each tile's box by 0.25–0.3 m past the tile on every side so neighbours overlap, and fade each box's alpha to 0 over that overlap so the tiles cross-fade with no hard border. Alternatively, use one projector for the whole patch.

**(4) Pacing: FAIL.**
- **c04a A2 (4.0 s, nothing happens for the full 4.0 s).** sa2_1 and sa2_3 show the same dark pine silhouettes. No tops turn gold, no light comes down the trunks, and there is no road or iron in frame, so the "sun clears the ridge" beat never plays. **Fix:** cut A2 to 2.2 s (the reeds line ends 1.7 s in, plus 0.5 s). Otherwise, key the gold sweep so it is visible from 0.5 to 2.5 s.
- **c01 6a.** The still tail is 2.1 s, over the 1.5 s cap. Cut 2.4 to 2.0 s.
- **c01 s11.** The ~1 s mid-action freeze, covered under (b).
- **c01 8b.** 12.4 s on a near-static close-up with no camera move logged; narration carries it, but it gives people time to pick at her face. Add a 0.05 m slow push like A7's.
- **c04a A7.** A 1.5 s tail is right, but the shot note still says "hold 3 s". Change the note to 1.5 s so a later pass doesn't put it back.
- **Trims that are fine:** c03 s2 (3.3 s, the warden is still moving), c03 3b (1.6 s tail), A3 (1.0 s tail).
- **Unverified.** `pace_k4.txt` has no rows for c02 or c04b: `pace.py` crashed on missing `logs/k2c02.log` and `logs/k1c04b.log`. The c02 s2/s3/s10 and c04b B4a trims are unchecked until it is re-run with the right logs.

**New problems visible at 1:1**
1. **Neck seam on the new body.** There is a jagged, stair-step skin edge on the left of her neck in c01 s8_3 (x≈720–760, y≈680–780) and s8b_3 (x≈800–850, y≈780–930). A small white shard pokes out at the right of her neck (s8_3 ≈1085,740; s8b_3 ≈1300,870). There is a pale ragged patch below her ear in s10_1/2 (≈960–1010, 540–610). **Fix:** re-blend the head–body join after the 3 cm drop by sinking the head's neck stump under the body's neck, or move the seam into the collar.
2. **c03 s11_1/2:** Grimtunnel speaks G3 with his head out of frame. Only his arm and loincloth show, and the heart floats behind his arm instead of in his hug. **Fix:** raise the aim about 0.4 m to his head and shoulder.
3. **c03 s10:** the shot is so tight on his face that the heart in his arms and the lamp swinging up into her face are out of frame. It is also a low angle looking up at him, where the note says "from her eye height, down at him". **Fix:** pull back about 0.5 m and raise the camera to her eye height.
4. **c01 s10_3–6:** firelight puts two hot orange specular spots on the lower edge of each breast cup (≈740,910 and ≈850,900), which read badly at 1:1. **Fix:** clamp the fire light's specular on that armour material.