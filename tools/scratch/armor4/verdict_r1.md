**Verdict: FAIL.** The plain top is well made: the cups fit, the rim and rivets read, the skin edges are clean and the LOD is clean. Four things fail on the armor side. The tiers don't climb, the steel turns blue at night, the mixed look pinches the gore, and no frame shows the fit in motion. Every frame also fails the gate on things outside armor (list at the end).

| Frame | Gate | Why | Checklist | Result |
|---|---|---|---|---|
| j_plain_close | NO | Skin waxy and evenly lit; hair a solid cap; NPCs and town kit a lower tier than her | 2✓ 3✓ 4✓ 5✓ | FAIL (not armor) |
| j_etched_close | NO | Same | 1: tells apart; 3: pattern ✓ but reads as matte black ribbon (F2) | FAIL |
| j_gilded_close | NO | Same (the blink is capture timing) | 1✗ not a step above etched (F1); 3✗ band reads flat | FAIL |
| j_plain/etched/gilded_look | NO | Steel blue in firelight (F3); stiff arms-out idle. These frames are the Calling tab, not Look | 1✗ tiers can't be told apart (cups about 40 px) | FAIL |
| j_*_play, crop_j_{plain,etched,gilded}_play | NO | Flat, empty plaza; she reads well | 1 accepted; 2✓ | FAIL (environment only) |
| j_gilded_run_play, its crop | NO | Pond is a hard-edged faceted polygon; flat unlit tree cards; bare ground | — | FAIL, restage |
| j_gilded_run_close | NO | Shield hides the top; hard-edged soil patch; flat grass cards in front | 4 can't be checked | FAIL, restage (F5) |
| j_gilded_fight_play, its crop, lod_on_fight_warden | NO | Canopy covers about 90% of the frame; cartoon pines clash with her; the see-through hole shows | 4 can't be checked; 6✓ | FAIL, restage (F5) |
| j_gilded_side_look | NO | Sword reads as a black bar (F4); steel blue (F3) | 4 band at rest ✓ | FAIL |
| j_gilded_deep_close | NO | Skin waxy, chest looks oiled; steel goes nearly white | 2? (F6); 5✓ | FAIL |
| j_gilded_fair_close | NO | Skin and hair as above | 5✓ | FAIL (not armor) |
| j_mix_stalker_close | NO | Gore plate reads as a bent sliver (F7); skin and hair | 3✓; 4✗ | FAIL |
| j_mix_stalker_look | NO | Steel blue (F3) | 4 seam ✓ | FAIL |
| lod_cmp_warden/arcanist/stalker/reaver | n/a (crops) | No difference visible in any pair, Reaver's fur and loincloth included | 6✓ | PASS |

**Causes and fixes**

- **F1 (armor): gilded is the quietest tier, not the loudest.** At the close camera the 5 mm band is a 3–4 px pale line and the sapphire about 5 px. The warden's pauldrons, bracers and skirt already have gold trim and gold rivets, so gilded just matches the set, while etched's black band is the bigger change.
  - Gild the whole rolled rim and the gore plate.
  - Make the band about 12–15 mm with a half-round bead, so it shows a lit line over a shadow line.
  - Make the sapphire 12 mm or more, in a gold setting (10+ px at the close camera).
  - Done when the three, side by side at the close camera, rank right at a glance.
- **F2 (armor): the blackened band reads as sewn-on ribbon.** It doesn't shine like metal. Give it metallic 1, a dark base color and roughness about 0.45 so it picks up some sky sheen. Add leaf shapes so the vine stops reading as a zigzag.
- **F3 (environment lighting; armor checks the result): steel goes blue at night.** At the creation camp the steel picks up the blue sky, and highlights on the fire side stay white-blue instead of amber. Check the campfire light's specular and strength against the sky's ambient and reflection at the camp. Number wanted: the average hue of the brightest 2% of metal pixels on her fire side.
- **F4 (armor, weapon metal): the blade mirrors the dark sky.** Hold it to the worn-metal standard: rougher, so it picks up firelight.
- **F5 (staging): no frame shows the fit in motion.**
  - At the close camera, from 3/4 on the sword side, shoot the top of an overhead swing and a mid-stride run frame with the shield arm out.
  - Restage the play-camera fight in a clearing, and move run_play away from the pond, or cut both until environment fixes them.
- **F6 (number needed): deep-tone steel.** Need the share of cup and pauldron pixels at sRGB 250+ in deep vs fair, and the average cobble brightness in both. That tells whether the exposure shifted or it's only contrast with dark skin. If exposure moves with her skin tone, lock auto-exposure at the close camera.
- **F7 (armor): gore plate in the mixed look.** Around x1040, y930 it reads as a bent sliver; the warden's is a neat plate. It is probably weighted to the breast bones and squeezed by the stalker's arms-in idle. Weight it rigid to the chest bone and recheck in that idle.

The three `_look` frames are on the Calling tab, not the Look tab. If the Look tab frames her chest, re-shoot the tiers there.

**Per item**
1. **Tiers: FAIL.** Gilded doesn't read as a step up (F1), and the Calling camera can't tell the three apart.
2. **Metal: FAIL at night (F3).**
   - Day passes: not chrome or plastic, darker than her fair skin, and the gold reads as gold.
   - Deep tone waits on F6.
   - Plain forged looks machine-pressed. Hammer marks in the roughness would sell "forged".
3. **Form: FAIL on the gold band,** which doesn't read as raised at 1:1. Rim and rivets PASS; the vine reads as a pattern (PASS; see F2).
4. **Fit: FAIL (F7).** Standing fit passes; fit in motion is unshown (F5).
5. **Skin edges: PASS** at the deep and fair tones.
6. **LOD: PASS** for all four callings.

**Outside armor, failing the gate**
- **Face/skin:** waxy, evenly lit skin on her face and torso in every close frame; at the deep tone the chest looks oiled.
- **Hair:** a solid cap with a hard line at the forehead and temples at the close camera; a dark strand line down her neck in j_mix_stalker_close (about x975, y630).
- **Animation:** the warden's Calling idle holds both arms stiffly out, like a mannequin.
- **Environment:**
  - j_gilded_run_play: the pond's hard faceted edge, and the flat unlit tree cards.
  - The fight frames: canopy over the fight, with the see-through hole showing.
  - j_gilded_run_close: the hard-edged soil patch and grass cards.
  - The play-camera town plaza is empty.
  - Town NPCs and kit sit at a visibly lower detail level than her.
  - The camp lighting on metal (F3).