p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\tools\anim\crowd.py"
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


# The axe raised high, the haft angled up and back over the head: from the
# game's camera an axe hung behind the back is hidden by the body.
rep('''        # (the axe head hung down behind the back, the shield arm flung wide),''',
    '''        # (the axe raised high, its head up and back over the shoulder, where
        # the camera above sees it; the shield arm flung wide),''')
rep('''axe((-0.18, 1.80, -0.24), (0.0, -0.85, -0.5),''', '''axe((-0.16, 1.88, -0.12), (0.0, 0.62, -0.78),''')
rep('''axe((-0.17, 1.78, -0.30), (0.0, -0.93, -0.35),''', '''axe((-0.15, 1.86, -0.18), (0.0, 0.45, -0.89),''')
# The get-up a little quicker: up and settled 0.67 s after the blow.
rep('''        (37, dict(hips=hips(0.40, 51, -0.05)''', '''        (36, dict(hips=hips(0.40, 51, -0.05)''')
rep('''        (44, dict(hips=hips(0.70, 28, -0.05)''', '''        (42, dict(hips=hips(0.70, 28, -0.05)''')
rep('''        (50, dict(hips=hips(0.90, 6, -0.05)''', '''        (47, dict(hips=hips(0.90, 6, -0.05)''')
rep('''        (54, dict(hips=hips(0.92, 4, -0.05), spine=(0, 4, 0)),''', '''        (50, dict(hips=hips(0.92, 4, -0.05), spine=(0, 4, 0)),''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
