p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\docs\cinematics\shoot\c03.md'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)


rep("- **Action:** he goes down on his knees in the river on `Fixing_Kneeling` (from 0.8 s, at 0.25, blended over 0.9 s). At 1.4 s the greatsword leaves his right hand. The lamp stays in his left.",
    "- **Action:** he goes down on his knees in the river on animation's `folk/m_kneel_lamp` (blended over 0.6 s); it runs on through shots 3 and 3b. At 1.4 s his sword hand opens and the greatsword leaves it. The lamp stays in his left, held up; he looks at it, and at 6 s (inside shot 3) the arm starts to shake.")
rep("- **Camera:** low from her side (`w` plus (0.8, 0.8, 2.2)), up at his head, focus on the eyes at f/2.8.",
    "- **Camera:** low from his right (`w` plus (-0.9, 0.8, 2.2)), up at his head, focus on the eyes at f/2.8. From his left the lamp, held up, stood in front of his face; from his right its light still falls across it.")
rep("""  - the nod is played on her lids as a stand-in: down to 0.6 at 0.9 s, open again at 1.6 s. The real nod (head down 8°, held 0.4 s) is to be keyed.""",
    """  - at 0.9 s she nods once, slowly (animation's `her/nod`, laid over her stance).""")
rep("""- **Camera:** from the south-east (`w` plus (2.8, 1.0, 2.2)), on his left hand and the lamp hanging under it.
- **Action:** at 1.1 s the lamp's flame goes out and his eyes go dark over 0.4 s (`lamp`: unlit, glow 0). The lamp-iron itself stays in his hand.""",
    """- **Camera:** low beside his left fist (the hand plus (1.6, -0.6, 1.4)), tracking the lamp as it goes down.
- **Action:** he lowers the lamp into the river on `folk/m_lamp_down`; it meets the water at 1.1 s, and the flame goes out and his eyes go dark over 0.4 s (`lamp`: unlit, glow 0). It sinks under. The lamp-iron stays in his fist.""")
rep("""  - he goes down into the water on `Death01` (from 0.4 s, at 0.45);
  - at 2.6 s the heart is set under the water over his chest (`w` plus (0, 0, -2.4), at y -1.25) and comes up to 0.35 of its light over 1.2 s, so the water lightens from beneath.""",
    """  - he folds forward into the water on `folk/m_fold_forward` and lies face down at her feet;
  - at 2.6 s the heart is set under the water at his chest (`w` plus (0, 0, 2.0), at y -1.25) and comes up to 0.35 of its light over 1.2 s, so the water lightens from beneath.""")
rep("- **Camera:** from the east of his body (`w` plus (1.8, 0.9, -0.8)), tracking the heart, with a slow push of 0.6 m.",
    "- **Camera:** from the east of his body (`w` plus (1.8, 0.9, 3.2)), tracking the heart, with a slow push of 0.6 m.")
rep("- **Shot 5:** he falls back, not forward (the stand-in `Death01`). The heart therefore rises where his chest lies, 2.4 m north of where he knelt, which gives it farther to drift to her in shot 7.",
    "- **Shot 5:** he folds forward and lies face down at her feet (`m_fold_forward`), toward her. The heart rises from his chest, 2 m from her, so its drift to her hand in shot 7 is short and close.")
rep("""  - the Warden's `kneel_fall` (the knees, the arm lowering, folding forward);
  - her `reach_flinch`, and the nod (to key by hand);""", """  - her `reach_flinch`;""")
rep("- **The heart:** it is a glowing sphere for now. It should be a faceted stone, cold and very bright, water running off it. Its glow should lean toward her fingers and stretch toward her out of his arms.",
    "- **The heart:** it is a rough-cut stone of a few faces now, with the light inside and a ring of glow about it. Still to come: water running off it, and its glow leaning toward her fingers and stretching toward her out of Grimtunnel's arms.")
open(p, 'w', encoding='utf-8', newline='\n').write(t)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\docs\cinematics\shoot\c04a.md'
t = open(p, encoding='utf-8').read()
rep("""  - at 4.4 s the cold reaches her: `squint` 0.2, `frown` 0.2, and a shiver's `cloth`.""",
    """  - at 4.4 s the cold reaches her: `squint` 0.2, `frown` 0.2, and one hard shiver (animation's `her/shiver`, laid over her stance) with its `cloth`.""")
rep("""- **To come:** the breath-smoke (none shows yet), the colour coming into her face, and the shiver's tremor.""",
    """- **To come:** the breath-smoke (none shows yet), and the colour coming into her face.""")
open(p, 'w', encoding='utf-8', newline='\n').write(t)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\docs\cinematics\shoot\c01.md'
t = open(p, encoding='utf-8').read()
rep("""  - at 1.2 s the long exhale, `mouth_open` 0.2 and `brows_sad` 0.4 over 1.2 s, easing to 0.05 and 0.2: something almost arrives, and doesn't.""",
    """  - at 1.2 s the long exhale (animation's `her/exhale`, laid over the kneel), `mouth_open` 0.12 and `brows_sad` 0.4 over 1.2 s, easing to 0.05 and 0.2: something almost arrives, and doesn't.""")
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')
