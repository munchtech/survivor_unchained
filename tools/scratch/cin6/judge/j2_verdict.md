# Verdict: her face's lighting in the close shots (cinematics 2, round 1)

Judged at 1:1 only. Offsets are from her eyes bone: x = her left, y = up, z = straight out of her face. Items 1, 2 and 4 fail; item 3 passes. For C02 s8 I pick the frontal 100 mm framing, but the lamp has to move.

**1. Eye light (0.3, #fff3e6, just above the lens): FAIL at s8; A5 can't be judged; s8b and A7 pass**
- **s8b and A7:** her eyes read alive. The iris colour and the whites show, there is one catchlight per eye high on the pupil, no hotspot and no wrong second catchlight.
- **s8:** her eyes read alive, but the light flattens her. Her left cheek and jaw on screen were in shadow in the before frame; now they are lit almost as much as the right side, so the close-up looks lit from the front. The warm ember glow at frame-right in the before frame is also gone, so the added lights now carry her face.
- **A5:** her eyes are shut in the after frame (open in the before at the same frame number). Recapture a frame where they're open.
- **Change, all four shots:** keep 0.3, the colour and the position. Narrow the cone so its edge is about 0.07 m from the point between her eyes (about 5° from 0.8 m), aimed there. For A7's push, size it for the closest point. She keeps the catchlight and the iris lift, s8 gets its shadow side back, and A5/A7 stop looking a shade paler than the dawn around her.

**2. Warden's lamp at 1.0, #a8d2ff (C02 s8): FAIL**
- It's better than 2.0, but the hair nearest the lamp still bleaches to cream or tan: the strip behind her ear in the left three-quarter frame, and the top-left hairline in the frontal one. Only the hair on the far side from the lamp, in the 135 mm frame, reads brown.
- Her skin is still grey-white on both cheeks, warm only at her ears and nose tip. There is no blue side and no red side.
- No framing shows the flame in either eye, and both eyes have dark sunken crescents under them. The light seems to come from above and in front, so its reflection hides under her lids.
- **Change:** move the light rather than dim it further (see 5).

**3. Warm fill (0.25, #ffc890, under her left eye, s8): PASS.** The grey-violet bruise under that eye is gone. It reads as skin, with no warm pool, hotspot or extra catchlight.

**4. Crown rim (0.8, #b9c9ff, from above and behind, s7): FAIL**
- No rim shows at 1:1. The hair is the same flat "helmet" dome, if anything a shade more evenly lit. In this over-the-shoulder shot "behind her" is on the camera's side, so the light fills the back of her head instead of edging it.
- **Change:** put it on the far side of her head from the camera, at [0, +0.45, +0.50], aimed back at her crown, so the light and the camera are about 140° apart at the crown edge.
  - Energy 1.5, because her crown sits against the brightest frost in the frame and 0.8 can't show there.
  - Keep #b9c9ff.
  - Cone about 20°, so only the crown and the side edge of her hair catch it.

**5. C02 s8 framing: frontal 100 mm (k6front_c02_s8_2.png)**
- It's the only one with both eyes (for the flame in each) and her lips (for the breath) where her face is clear of the band.
  - The 135 mm frame cuts off just under her nostrils, and its band on the left edge looks like a black-bar error.
  - In the left three-quarter frame the band touches her ear and seems to cut her head.
- The band can't stay as it is. A pure-black bar next to its own lamp reads as a cut-out, not as iron.
- **Change: move the lamp, not the camera.** Put the lamp (the iron and its light together) at [−0.20, +0.06, +0.28]. That's 0.20 m to her right (frame-left), just above her eye line, 0.28 m toward the camera: about 35° off the lens and about 0.35 m from her face.
  - The iron drops out of the frame at that depth.
  - The flame lands small in both eyes (the light's specular setting needs to be at least 0.5).
  - Her right half goes blue and her left half falls off.
  - The hair beside the flame stops being several times brighter than her cheek.
  - Use about 0.8 energy and keep #a8d2ff. If her left cheek still shows no ember red, raise her ember light there (about 0.15).
- **If the lamp can't move:** keep the frontal framing, still move its light to eye height about 35° off the lens, and let the lamp light reach the iron so it shows a lit inner edge instead of a black bar.
- None of the three framings shows the wet hair or the green weed the note asks the light to find.

**New problems visible at 1:1**
- **C02 s8 (frontal and left three-quarter):** the lamp's light on both shoulder guards makes hot white patches in the bottom corners that compete with her face. End the lamp's cone at her jaw (about 20° from 0.35 m).
- **C01 s8 and s8b:** there is a hard, stair-stepped pale patch on her neck left of her chin (s8 around x 720–770, y 690–800; s8b around x 800–860, y 780–930). It reads as torn skin. It's already in the s8b before frame, so it comes from a shadow cast by one of the shot's existing lights, not from the new rig. Soften that light's shadow (light size about 0.05 m, or shadow blur about 2) or raise its shadow resolution for these close-ups.
- **C01 s8:** the ember glow is missing from the after frame, and her warm side went with it. Check the shot's timing before retuning s8.