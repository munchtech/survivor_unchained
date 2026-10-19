**C01 verdict (k13, round 3: the confirmation).** I calibrated on o1, o2 and o3 first (all NO). Every frame was opened once at 1:1.

**Per shot**
- **c01 s1:** passed earlier. Not re-judged.
- **c01 s3: NO as it stands, and it can't be cut.** It is the scene's first picture; without it the scene opens on her already sitting up.
  - In _3 her eyes open, which is the point of the shot. Both irises read solid black with one catchlight: no iris color, and the whites are unlit. That gives doll eyes in an extreme close-up.
  - _1 and _2 (warm, freckled, sleeping) would ship.
  - Owner: STAGING (there is no eye light).
  - Frame-around: add s8b's eye rig from 0.0: `{"do":"rig","name":"eye","energy":0.2,"color":"#fff3e6","angle":5,"from":{"lens":[0,0.25,0]},"aim":{"actor":"her","bone":"eyes"}}`.
  - Motion _1 to _3: a slow push and the lids opening. No snap, no slide.
- **c01 s6: CUT. NO (touch-up only).**
  - Three clipped white hot spots on the black armor (pauldron, breast cup, right bracer) glow like bulbs. They are the brightest things in a 6.4 s medium shot.
  - The skin on her arms and thighs is flat and waxy, her lips are parted in _2, and there is no cord or flask in her hands for "looks down at her hands".
  - ENV also has a flat gray disc on the log end at frame right.
  - TOUCH-UP brings it back (armor metal, skin, the Reaver cord).
  - Neighbors as played: s3 to s8. The cut works as a time cut. It goes from the lying extreme close-up to a frontal close-up of her upright, a different angle and size, so it is not a jump cut. The bedroll line moves to the end of s3.
- **c01 s7: CUT.**
  - The shot exists to show the prints for "Prints in the frost..." and none is visible at 1:1: only frosted grass tufts and black trees.
  - A pale, bone-like branch hangs at top center.
  - Owners: ENV (prints dark, wet and big enough to read from a low camera, with the grass flattened along the trail) and STAGING (re-aim).
  - Neighbors: s3 to s8, as above. The prints line moves to s8, where her eyes go from the trail to her boots: that is the line's picture.
- **c01 s8:** passed, unchanged. It now carries the prints line.
- **c01 s8a: SHIP.**
  - A handsome night extreme long shot: silhouetted pines frame the wall, with three blue ford lamps, soft halos and stars. The tier-2 trees and wall look right in darkness and silhouette.
  - The high gold lamp reads like a warm star because no tower shows under it. It still works: it is the only warm light, it sits centered, and the line names it.
  - It now carries the whole lamp line and the call (see the fixes).
- **c01 s8b: CUT confirmed.**
  - Slack parted lips (no lip-close shape exists), and a huge, flat, waxy forehead cropped at the hairline, with the hair's hard edge at her temple.
  - Owner: TOUCH-UP (lip-close shape, skin, hairline).
  - s8 can't carry its lines: s8 plays before the lamp line starts, and it now holds the prints line. s9 is cut too.
  - s8a carries both: the narration runs to its end over the extreme long shot, then the far voice comes down the road while we look up it.
  - Neighbors: s8a to s10 works. It goes from the extreme long shot to the 0.35 s head-snap on the crack sound, with no jump cut and no broken eyeline.
- **c01 s9: CUT.**
  - The beat doesn't read. R1 lies flat beside the bedroll, warm-lit by the r1coal rig inside the firelight, so he reads as a sleeping camp-mate, not "a head coming up through the frost".
  - The top half is crushed black, she is a tiny back, the log's flat gray end disc sits beside her, and the foreground grass reads as flat cards.
  - Owners: NPC/ANIM (a rise that reads, head and shoulders through the frost), ENV (log end caps, grass) and STAGING (R1 lit cold, beyond the firelight).
  - Neighbors: s8a to s10 works once the crack sound lands at the end of s8a. The frost line moves to s12, whose crane shows the frost breaking. R1's spawn also lives in s9 and must move.
- **c01 s10: SHIP.**
  - A 0.35 s reaction flash: a clean warm profile with room in front of her toward the threat.
  - The clipped glints at the base of both pauldrons and the small notch in her temple hairline are TOUCH-UP items, and they don't read in 0.35 s.
  - Motion: her head is already turned at _1 and her chin lifts into the stand by _3. It reads as an intended snap, not a glitch, and there is no slide.
- **c01 s12: NO as it stands, and it can't be cut** (it is the hand-over into play).
  - The first second fails. Her face is frontal and lit only by the low fire at exposure 0.414, so it reads heavy-jawed, dark-eyed and masculine, not the heroine of s3 and s10.
  - A pale square sprite with snowflake specks floats over the sack at frame right (about x1320, y590). It looks like a particle with a missing texture.
  - In _2, R1 crouches as if sitting on air. In motion it reads as getting up.
  - Owners: STAGING (face light); the sprite belongs to whoever owns that particle, likely the risen's rise or frost burst.
  - Frame-around: add s8's passed key at 0.0: `{"do":"rig","name":"key","energy":0.8,"color":"#ffc79a","angle":20,"from":{"actor":"her","bone":"eyes","off":[-0.6,-0.38,-0.3]},"aim":{"actor":"her","bone":"eyes","off":[0,-0.03,0]}}`. Set the same rig to energy 0 at 2.0, when the crane is high. Fix or remove the sprite.
  - Motion _1 to _2 could read as a snap spin: she faces the lens at _1 and walks away, turned about 150°, a second later. Check that the "move" cue turns her over at least 0.4 s and not in one frame. _2 to _3 is a smooth crane.
- **Hand-over (ho 000, 010, 020, 030, 040): smooth, no jump.**
  - 000 to 009 is the crane's last rise: fast but continuous. ho_009 is the same file as s12_3.
  - 010 to 040 hold that exact framing while the bars retract, the title fades in and the risen close in.
  - Combat starts by 040 with no camera pop.

**Final cut list:** s6, s7, s8b, s9.
- s8a and s10 ship.
- s3 and s12 ship once their frame-arounds are in.

**Fixes before the MR**
1. **s3:** add the eye rig above.
2. **s12:** add the face key above (on at 0.0, off at 2.0), and get rid of the square sprite.
3. **Lines and cues moved because of the cuts** (timing only):
   - s3: `{"at":2.8,"do":"line","id":"cin_drowned_fire.bedroll"}`, `"fit":["cin_drowned_fire.bedroll"]`, `"tail":0.6`.
   - s8: `{"at":0.3,"do":"line","id":"cin_drowned_fire.prints"}`, `"fit":["cin_drowned_fire.prints"]`, `"tail":0.7`.
   - s8a:
     - `"fit":["cin_drowned_fire.lamp","cin_drowned_fire.call"]`, `"tail":0.8`.
     - `{"at":"after:cin_drowned_fire.lamp+0.5","do":"line","id":"cin_drowned_fire.call"}`.
     - Camera `"move":{"push":0.04,"ease":"linear"}`, so about 10.5 s of the extreme long shot doesn't sit dead.
     - `{"at":"end-0.4","do":"spawn","actor":"r1","def":"risen","mark":"r1","style":"rise"}`, so R1 has about the 0.4 s of rise he had before s10 freezes him.
     - `{"at":"end-0.3","do":"sfx","name":"frost_crack","gain":0.8}`, so the snap in s10 has its sound.
   - s12:
     - `{"at":0.3,"do":"line","id":"cin_drowned_fire.frost"}`.
     - Its mist fades refer to mists created in s9 ("west", "north"): either create them in s12 or drop the fades.
   - Look at these once yourself: R1 still coming up in s12 _2, and the longer s8a.

**The set as a whole.** C01 works where darkness and brevity do the job: s8a, the s10 flash and the hand-over. It fails where she is lit for seconds at mid-range (s6, and s8b's close-up) or where the shot's subject never reaches the screen (s7's prints, s9's rise). The recurring blockers belong to other leads:
- TOUCH-UP: the clipped armor highlights and the parted-lip rest shape.
- ENV: the flat gray log end caps and the top-down frost, which reads as cotton wool across most of the play view at the hand-over.