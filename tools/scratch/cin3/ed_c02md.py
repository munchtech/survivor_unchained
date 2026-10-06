p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\docs\cinematics\shoot\c02.md'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)


rep("""  - he comes up through the surface (1.2 s) and gets up on `LayToIdle` at 0.45 speed: head first, sitting, then standing;""",
    """  - he comes up through the surface (1.2 s) and gets up on animation's `folk/m_rise_stiff` (Kimodo): on his back, he sits up by 1.9 s, rests on his knees to 2.7 s and stands by 3.8 s, every movement a tired man's, made enormous. The lamp stays out of the water throughout;""")
rep("""- **Action:** he lifts the lamp on `Idle_Torch` (0.4 speed), the left fist high and toward her. She does not step back: her gaze goes up into it (0, -0.6), `squint` 0.3.
- **Sound:** `mystery` to 0.8; at 2.0 s the tremble's rattle (`hit`, quiet).
- **To come:** `bend_lift` (Kimodo) for the long bend down to her face and the tremble.""",
    """- **Action:** the long bend down to her on animation's `folk/m_bend_lift` (Kimodo), the lamp lifted to her face; its tremble peaks at 2.0 s, on the rattle. The clip holds alive through shot 8. She does not step back: her gaze goes up into it (0, -0.6), `squint` 0.3.
- **Sound:** `mystery` to 0.8; at 2.0 s the tremble's rattle (`hit`, quiet).""")
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')
