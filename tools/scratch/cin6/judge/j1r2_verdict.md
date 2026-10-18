**Verdict: cinematics 3, round 2 (C01 to C04).** Four of seven items pass: (g) except A7, (5), (a), and the recoil in (2). (b), C03 s10/s11 and three pacing trims fail. Everything below is from the 1:1 frames.

**(b) C01 end: FAIL**
- **s11 opening:** still 1 has her upright with empty fists, not mid-bend. Stills 2 and 3 are the same pose (0.0 cm apart), with the sword already level at her hip, so no still shows a bend. The pop and the freeze are still there.
  - Fix: check whether still 1 is drawn before the 0.0 clip takes effect. If the game's first frame matches it, apply `PickUp_Table` on frame 0 from its deepest-bend frame.
  - Move `@idle` from 1.0 s to the clip's end, (clip length − 0.45)/1.1, with blend 0.25.
- **s11 blade tip:** stills 4 to 6 (about 1.1 to 2.2 s) still plant the tip on top of the log.
  - Fix: at 0.8 s add `{"do":"move","heading":-1.75,"dur":0.4}` so she "comes round with it ready" toward r1, as the note says. That swings the blade off the log.
  - Then cut s11 from 2.2 to 1.8 s; stills 4 to 6 move only 0.4 to 0.6 cm.
- **s12 framing:** still 1 crops her above the lips, with her eyes out of frame. In still 2 she is not in frame at all (the camera is on empty ground by the fire). In still 3 she is only a sliver in the bottom-right corner. The aim is not following her visible body during the crane.
  - Fix: aim at the body she plays as from t=0 (the `play` cue at 0.0 swaps bodies).
  - At still 1 she is only about 1.6 m from the lens. Start the crane at least 3.7 m from her chest (MLS at 35 mm, knees to head).
  - Re-shoot stills at 0.0, 0.5, 1.0 and 1.5 s.
- **Into play:** the hand-over itself passes. On the sheet she stays in the same spot from 000 to 040 and the bars clear cleanly.

**(g) Crops: PASS for A3, A5 and C01 s10; FAIL for A7 (small)**
- A3, A5 and C01 s10 have good headroom and eye lines.
- A7 places her eyes about 19% down the picture, with the forehead cut just above the brows and about 180 px of neck below. A5 sits at 28%.
  - Fix: A7 aim offset y from -0.05 to -0.03.

**C03 s10 / s11: FAIL**
- **s10:** all three stills run from Grimtunnel's chin to his crotch. His head is out of frame, yet every beat in the note is head acting (looks, sniffs, near-bow, grin).
  - Fix: pos off [0.7,1.55,0.2] → [0.85,1.75,0.65]; at off [0.35,1.0,-1.25] → [0.35,1.38,-1.25]; keep lens 28. That is about 2.0 m and frames the heart to the hat top.
  - Check her shoulder doesn't clip the left edge; if it does, x 0.85 → 1.0.
- **s11:** his face is in now (hat brim cut, acceptable), but her eyes are above the top edge in all three stills, showing only her nose and mouth.
  - Fix: pos y 1.2 → 1.38; at y 1.0 → 1.18.

**(2) C03 s9 recoil: PASS on the recoil, FAIL (small) on the tip**
- The guard is upright and alert, not limp, and it holds through s11.
- At 1:1 the blade tip ends exactly on the outline of the warden's hood, so it reads as resting on the corpse. I can't see depth from one view.
  - Fix: turn her heading 0.26 rad away from the warden in s9 (and carry it into s10 and s11), so the tip clears his outline by at least 100 px.

**(5) Frost: PASS**
- I see no tile grid in s12 stills 4 to 6, ho_036 or ho_040; the patches blend softly.
- One straight-edged bright patch sits by the gallows lamp, bottom right of s12_5/6 and ho_036/040. I can't tell from these stills whether it's the posts' shadow or a frost tile edge. If it's a tile edge, use the one-decal fallback.

**(a) C03 into C04 A, and the C04 A hand-back: PASS**
- The cut and the walk-out flow continuously.
- In the hand-back she stays in place under the title while the ember nova fades.

**(4) Pacing: FAIL on three cinematics**
- c01 6: 7.0 → 6.4 (1.6 s tail after the 5.4 gaze; the last stills move 0.8 cm).
- c01 11: 2.2 → 1.8, together with the turn in (b).
- c02 2: 3.0 → 2.4, but read the shot's note first; I didn't read the C02 notes for lack of context room. No cue after 0.0, and the second half moves only 1 to 2 cm.
- c03 3b: 2.5 → 1.9 (1.6 s tail; both actors move 1 to 3 cm).
- c04a A2: 2.4 → 2.2, as round 1 asked.
- c04b B4a: 2.2 → 1.7. No motion data for this shot, so this rests on the cue numbers only. Keep 2.2 only if its note makes it a narrative beat.
- c04b B4b: 2.0 → 1.7 (same caveat).
- **Keep as they are:**
  - c01 5: she is moving.
  - c01 6a: "it stays", a 2.0 s narrative beat.
  - c03 12: the end-of-scene groan and dawn pause, 1.2 s.
  - c04a A7: 1.5 s silence with the push, as the note asks.
  - c02 5, 7, 9, 10 and c03 2: the warden is moving.
  - The follow shots are exempt.
- No round-2 trim cut a narrative pause too short.

**New problems visible at 1:1, worst first**
1. **C03 s9 to s11, the heart is never held.** It floats in front of Grimtunnel's belly (s9, s10) and in mid-air beside him (s11) while his arms hang at his sides. The note says he "hugs it to his chest".
   - Fix: attach the heart to his hands, or move it between his hands and give him a cradle or hold clip from 0.5 s.
2. **C03 s9 to s11, the heart's light blows out his torso** to flat pink-white with no form.
   - Fix: at s9 start add `{"do":"lamp","actor":"heart","glow":0.4}`.
3. **C03 s9 to s11, he stands at full height in shin-deep water.** The notes have him "up to the waist", and that height mismatch is why s10 can't look "down at him". If you sink him about 0.55 m instead, re-check the camera numbers above.
4. **C01 s11 still 2:** the sword and shield on the log are still fading out while the sword is already in her hand. Make the prop removal instant.
5. **C04A A5 still 3:** a jagged pale edge at the base of her neck. It's the same head-neck join as the excluded C01 mark; add A5 to the outfits area's re-shoot list.

All frames are in `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92\godot\.shots\` (prefix k8; sheets in `j1k8\`). I didn't open the C03 s12 frames, to stay inside the context budget.