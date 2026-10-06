import os
p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'c07_hammer_stops.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b)


rep("who matter only in shot 14.", "who matter only in shot 12.")
rep("Line `brannoc.nell` begins, in time with the strokes: one phrase between blows. | 9.0 |",
    "Line `brannoc.nell` begins, in time with the strokes: one phrase between blows, five phrases (to \"...by dark.\"). | 13.0 |")
rep("""| 10b | CU | 85 | Static, low, up at him: the one close shot of his face, half in the hearth's light, eyes catching it | *"She'd got up with the others. I put her down."* Line `brannoc.nell_risen`. He looks at her properly for the first time. "Was it quick?" Choice. | 6.0 + choice |""",
    """| 10b | CU | 85 | Static, low, up at him: the one close shot of his face, half in the hearth's light, eyes catching it | *"She'd got up with the others. I put her down."* He looks at her properly, for the first time. Silence. (The close-up is for the look, not for a line: he has no face rig yet.) | 2.5 |
| 10c | MS | 50 | Static, from her side | Line `brannoc.nell_risen`: "Got up. ...Got up, and you put her down. ...Was it quick?" Choice. | 5.0 + choice |""")
rep("- *10a / 10b.*", "- *10a / 10b / 10c.*")
rep("One close-up of his face (shot 10b)", "One close-up of his face, silent (shot 10b)")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
