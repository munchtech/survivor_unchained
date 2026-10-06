p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\docs\cinematics\shoot\c01.md'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)


def cut(start, end, new):
    """Replace from the line starting with `start` up to (not including) the line starting with `end`."""
    global t
    i = t.index(start)
    j = t.index(end, i)
    t = t[:i] + new + t[j:]


rep("(previs pass 3, 4 October 2026). It runs about 68 s with the narrator's placeholders.",
    "(previs pass 4, 5 October 2026: animation's three clips in place of the log). It runs about 69.5 s with the narrator's placeholders.")
rep("She wakes prone, head north, between the fire and the log (`lie`, -9.1, 91.05).",
    "She lies curled on her right side at the fire ring's east edge, her face to the embers (`lie`, -9.65, 90.90, turned so the clip's front faces the fire). She wakes, comes up onto her elbow and kneels back on her heels where she lay; she never sits on the log.")
rep("Shot 5 shoots through the embers from the west, and it is the one shot on the fire's far side. It is a look *at* her from where the cold is not, and she is still lying down, so no eyeline is crossed.",
    "Shots 3 and 5 shoot across the ring's edge from the north-west, and shot 6 across the embers from the south-west: she faces the fire, so her face is only to be had from the fire's side. She is lying or kneeling and looking down, so no eyeline is crossed.")
rep("three close-ups (3, 8, 8b) and one MCU (6) carry her face. Two inserts (2, 4) carry the body's wrongness without a face.",
    "three close-ups (3, 8, 8b) and one MS (6) carry her face. The top shot (2) and the hand at the coals (6a) carry the body's wrongness without a face.")
rep("through shots 2 to 8b, with nothing moving but the camera's sink and push.",
    "through shots 2 to 8b. Nothing moves but the camera's sink and push, and her slow waking: lying, the elbow, the kneel and the reach, each in its own shot.")

cut("### 0 · HOLD · 0.5 s", "### 1 · BLACK", """### 0 · HOLD · 0.5 s
Creation's last frame, held: her by the high fire, dry. Under it the scene is set:
- her hands are emptied, and her weapon (and shield) are propped on the log;
- she lies curled on her side on `lie`, on frame 0 of `her/lie_side_wake`, lids shut.

""")
cut("### 2 · TOP · 3.5 s (28 mm)", "### 5 · MS", """### 2 · TOP · 3.5 s (28 mm)
- **Camera:** straight down from 4.0 m over her and the fire ring, sinking slowly to 3.6 m (`slow` ease).
- **Picture:** the embers under the tripod, and her curled on her side at the ring's edge, her face to the coals and one hand out in the ash. The frost silvers the corners. This replaces the written ECU of a hair on a stone: that camera was inside the ring's stones, and this frame says more. She lies where no sleeper would, at a fire no one could bear.
- **Performance:** `her/lie_side_wake` from 0 at 0.24: the clip's two still breaths, slowed, run under this shot and the next.
- **Sound:** two drips.

### 3 · CU · 4.0 s (100 mm)
- **Camera:** low across the ring's north-west edge at (-11.05, 0.55, 89.22), on her face lying sideways, pushing in 0.1 m over the shot. Focus on the eyes, f/2.
- **Performance:** at 2.0 s her lids open over 0.15 s (`eyes_wide` 0.25, easing to 0.05). No gasp, no start. Blinks are held until 2.2 s.
- **Picture:** half ember, half moon.

""")
cut("### 5 · MS · 3.5 s (35 mm)", "### 7 · OTS", """### 5 · MS · 4.5 s (40 mm)
- **Camera:** low (0.45 m) on the fire's far side at (-11.6, 0.45, 88.7), looking back across the embers at her.
- **Performance:** she comes up onto her right elbow, slowly, worn out (`her/lie_side_wake` from 2.4 s at speed 1). Her hair hangs.
- **Sound:** `cloth_water` as she moves.

### 6 · MS · 7.0 s (40 mm)
- **Camera:** front three-quarter from her left, across the embers, at (-11.1, 0.85, 91.6), tracking her chest as she comes up.
- **Performance:**
  - `her/sit_back_heels` from 0: from the elbow up onto her hand, her legs drawn round under her, onto her knees and back on her heels; her hands come up before her, palms up, and she looks down at them;
  - `brows_sad` 0.3, `mouth_open` 0.08;
  - gaze down at the flask on her wrist (0, 0.8), across to the bedroll at 1.6 s (0.5, 0.35), and down again at 3.4 s;
  - a slow blink at 4.8 s, then a look off at 5.4 s.
- **Sound:** N1 at 0.8 s, "Your bedroll has not been slept in."
- **To come:** the letter (Kimodo `letter`), and the 1.5 s look at her background's item (the hare, the lens, the kerchief, the lantern) when those props exist.

### 6a · INSERT · 3.0 s (50 mm)
- **Camera:** low from the south at (-9.95, 0.75, 91.35), across the ring's stones to the coals.
- **Performance:** `her/reach_coals`: her right hand goes out low over the embers, palm down, and stays, closer than anyone could bear. It does not pull back. (The written script's insert, shot 5. It comes after the kneel, because the reach is made kneeling.)

""")
rep("""- **Camera:** behind her, low over her left shoulder, looking down at the trail where it reaches the camp. From 0.4 s to 0.6 s before the end, it tilts up and north along the trail into the dark (`slow` ease), and the focus pulls with it.
- **Blocking:** she is turned toward the trail (`seat_nw`).""",
    """- **Camera:** behind her at (-9.55, 1.12, 91.45), low over her left shoulder, looking down at the trail where it reaches the camp. From 0.4 s to 0.6 s before the end, it tilts up and north along the trail into the dark (`slow` ease), and the focus pulls with it.
- **Blocking:** she stays kneeling; her head turns over her shoulder to the trail (`head`, over 1.2 s), and holds there through 8b.""")
rep("""- **Camera:** frontal, a little under her eyes, from the trail's side; the dark trees behind her.""",
    """- **Camera:** frontal from the trail's side, a metre off her eyes (the eyes plus (0.08, -0.02, -1.0)); the frosted grass and the dark trees behind her. Her face is lit from below by the embers.""")
rep("""### 8b · CU · 4.5 s, fitting the lamp line and the call (85 mm)
- **Camera:** as 8, a touch tighter.""", """### 8b · CU · 12.5 s, fitting the lamp line and the call (85 mm)
- **Camera:** as 8, a touch tighter (0.9 m).""")
rep("""- **Camera:** from the fire's side; the look tracks her head.
- **Performance:**
  - at 0.12 s her head turns hard to R1, screen left, with the gaze snapping across (`eyes_wide` 0.6, `brows_angry` 0.2);
  - at 0.75 s she is up, blending into her calling's idle as she steps off the log (`stand`).
  She is on her feet in one movement, without her hands. Kimodo's `kneel_to_stand_snap` replaces the blend when it lands.""",
    """- **Camera:** from her south-west at (-10.4, 1.1, 92.1); the look tracks her head.
- **Performance:**
  - at 0.12 s her head whips round to R1, screen left (`head`, 0.18 s), with the gaze snapping across (`eyes_wide` 0.6, `brows_angry` 0.2);
  - at 0.75 s she is up off her knees, blending into her calling's idle as she steps to `stand`; the head is let go at 1.4 s.
  She is on her feet in one movement, without her hands. Kimodo's `kneel_to_stand_snap` replaces the blend when it lands.""")
rep("""- **Shot 4** (the hand) is shot from above. The low insert was inside her arm. Until `reach_coals` exists, the hand lies at the coals rather than reaching for them.
- **Shots 6 to 9:** she sits on the log, not on the ground, until `lie_side_wake` and `sit_back_heels` exist. Every face shot was reframed to that eyeline.
- **Shot 6** is shot from her left (the fire's side) to keep the line.""",
    """- **She lies on her side and kneels where she lay** (animation's `lie_side_wake`, `sit_back_heels` and `reach_coals`), not on the log. Every face shot is framed on her bones, so it holds for any body (the male hero too).
- **The hand at the coals (written shot 5) comes after the kneel,** as shot 6a: the reach is made kneeling, and it now says more: awake, she holds her hand there on purpose. The top shot already shows the hand lying in the ash.
- **Shot 6** is shot from her left, across the embers, to keep the line.
- **Her looks are head turns** (the `head` cue), not turns of the body: kneeling, she looks over her shoulder at the trail (7) and whips round to R1 (10).""")
rep("""- **Motion** (animation, a1e3002b800ee55ac; Kimodo, awaiting the owner's run): `lie_side_wake`, `sit_back_heels`, `reach_coals`, `letter`, `kneel_to_stand_snap` and `take_from_log`.""",
    """- **Motion** (animation): `letter`, `kneel_to_stand_snap` and `take_from_log`. The tripod's legs cut across shots 5 and 6; the set wants a lower tripod or a hook on a stake.""")
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')
