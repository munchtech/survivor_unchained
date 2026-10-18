**Verdict, round 2: item 1 FAILS at C01 s8 only (s8b, A5 and A7 pass and can close); items 2 and 3 FAIL.** Numbers are pixel values read from the frames. Fine detail was checked on crops at the frame's own size, not enlarged.

**1. Eye light: s8b, A5, A7 PASS (close them). C01 s8 FAIL.**
- **s8b:** one live catchlight in each eye (L 211). The shadow side holds: cheeks 40 vs 128, a 3.2:1 ratio, the same as the k2 reference (3.1:1).
- **A5:** her eyes are open in _1, _2 and _3. One catchlight per eye sits at the top of the pupil (L about 195), and there is no hotspot.
- **A7 _1 and _3:** clean, matching catchlights at the top of the pupils.
- **s8 compared with k2:**
  - Shadow-side cheek went from L 35 to 76.
  - Forehead went from 75 to 165 and got paler (saturation 0.58 to 0.44).
  - Eye whites went from 18 to 53; the lit-to-shadow ratio dropped from 3.1:1 to 2.0:1.
  - Outside the cone nothing changed (neck under the jaw 98 to 91, pauldron 61 to 57), so the eye light did this. At this shot's distance the 5 degree cone still covers about 8 cm either side of the point between her eyes, the whole middle of her face (lower lip +68%).
  - It adds no catchlight here: k2 already had one in each eye from the ember (L 211), and k8's are the same (213).
- **Fix:** set the eye light's energy to 0 for C01 s8 only.
  - If her irises must show green, put the eyeball mesh on a spare render layer and set the eye light's cull mask to that layer, at 0.15.
  - Don't narrow the cone further: at about 2 degrees it would still light a band across her nose bridge and lids.

**2. Crown rim, C01 s7: FAIL.**
- At full size the crown is a smooth, out-of-focus copper dome with faint strand streaks, and there is no edge.
- Along its top edge (8 columns), brightness falls steadily from the frost (L 123-147) into the hair (50-80). No pixel at the edge is brighter or bluer than its neighbours, so the light isn't reaching the part of the head the camera sees.
- #b9c9ff is also the frost's own colour (blue exceeds red by 40-58 there, at the same brightness). Even a working cool rim would disappear against it.
- **Fix:**
  - Colour #ffd9b0, which the lamp up the road can justify and which stands out from the blue frost.
  - Energy 1.5 to 3.0.
  - Offset from her eyes bone (0.00, +0.30, +0.15): above and just in front of the crown, so it skims the top the camera sees.
  - Spot aimed at the top of her head (about 0, +0.12, -0.07), cone 25 degrees, range 0.6 m.
  - Target: a band 10-25 px wide along the top edge at L 170 or more, warmer than the rest of the hair. The background blur wipes out anything thinner.

**3. C02 s8: FAIL.** Only the far-side hair passes.
- **Wrong side:** the light lands on her LEFT (frame-right), and the nose shadow falls across her right cheek. The lamp and its iron are at frame-left; in _3 the lamp shows as a clipped white sliver at x 0-15. "0.20 m to her right" looks sign-flipped.
- **Blown out:**
  - Her left cheek is (254,238,213), with every sampled pixel clipped.
  - Forehead is 80-100% clipped and the nose bridge up to 82%.
  - Lips are washed out to about (215,178,172), against R1's (99,64,68).
  - The clipping removes the blue (cream, B/R 0.84), so there is no blue anywhere on her face.
- **Eyes:** no flame in either eye at full size. The irises glow a flat teal (mean L 160-198) with no bright point.
- **Ember:** no ember red on her left cheek, because that is the blown-out side. Her right lower cheek is a muddy brown-red shadow (78,41,33).
- **Hair:** the near hair at top right is beige (145,119,99) and reads as cream. The far hair is near-black, which is fine.
- **Black band:** still there, a flat (0,0,20) bar about 200 px wide at frame-left (x 245-520 across the three frames).
- **Pauldron:** the bottom-right one still has a clipped hotspot, with 14% of that corner above 235, the same as R1 (13.6%). The light changed sides and the hotspot didn't move, so this light isn't the cause.
- **Fix, lamp light:**
  - Offset x -0.20 (her right, the lamp's side), y 0.00, z +0.28.
  - Energy 0.8 to 0.25.
  - Keep #a8d2ff; go to #8cbcff only if the lit cheek still has less blue than red.
  - Keep the range ending at her jaw.
  - Turn the light's reflection on (specular 1.0) with a size of 0.01 m or less, so each eye gets a pinpoint flame.
  - Targets: lit cheek L 150-175 with nothing clipped and blue at least equal to red; lips at least 25 redder than blue.
- **Fix, ember:** yes, add it.
  - Energy 0.15, colour #ff6a33, offset (+0.15, -0.12, +0.18), range 0.30 m.
  - Target: her left cheek at L 45-60, with red at least 2.5 times blue (about a third of the lamp side).
- **Fix, band:** hide the lamp's iron in s8, or move it out of the 100 mm frame. Either keep the lamp's glow fully out of frame or let at least 60 px of it in, not a sliver.
- **Fix, hotspot:** render s8 with each light on the characters' layer switched off in turn to find the source. If none of them causes it, it's the sky reflection, which is for the outfits area.

**New problems from the light or framing, seen at full size**
- **C02 s8 framing:** the 100 mm crop shows only two slivers of hair at the top corners, so the note's wet hair and green weed can't read whatever the light does. Her eyes sit 18% from the top of the picture. If the weed matters, frame about 10% wider with her eyes near the upper third.
- **Not lighting, for your information:** the excluded head-neck join also shows in C04 A5 _3, as a faceted pale patch with a stepped edge at about x 720-800, y 720-900. Tell the outfits area.
- **Checked and fine:** the mottling on her right cheek in s8b is freckle texture in shadow, not a shadow fault.

The full-size crop sheet I judged from is C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\43e8c2e6-36a3-4fd7-8ca4-39c475e24666\scratchpad\j2r2\sheet_1to1.png