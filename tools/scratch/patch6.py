p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\emblems.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('''    e.lay(ellipse(gx, gy + 1, 15, 4.6), "glow", 1, 2, light=2.4)''',
    '''    e.lay(ellipse(gx, gy + 1, 15, 4.6), "glow", 1, 2, light=2.4, hue="#ffc070")''')
rep('''        e.lay(stroke(pts, 2.0, 0.4), "glow", 0.5, 0.6, light=1.2, z=2.5)''',
    '''        e.lay(stroke(pts, 2.0, 0.4), "glow", 0.5, 0.6, light=1.2, z=2.5, hue="#ff9a40")''')
rep('''def prompt(key, school):
    import icons
    import krea
    return LOOK + SUBJECT[key] + ", " + icons.SCHOOL.get(school, "") + ". " + krea.STYLE''', '''# Colours of its own where the school's words would drain it (steel's "cold white" painted the
# leap's stone and dust as a grey blur).
COLOURS = {"leap": "warm brown stone and dust colours lit hot gold and white from the impact"}


def prompt(key, school):
    import icons
    import krea
    return LOOK + SUBJECT[key] + ", " + COLOURS.get(key, icons.SCHOOL.get(school, "")) + ". " + krea.STYLE''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
