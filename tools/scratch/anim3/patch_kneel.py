p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\tools\anim\crowd.py"
new = open(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\anim3\kneel_new.py", encoding="utf-8").read()
s = open(p, encoding="utf-8").read()
mark = "# ------------------------------------------------------------------ the fallen --"
if "def kneel_aim" in s:
    a = s.index("# ---------------------------------------------------------------- the kneel --")
    s = s[:a] + s[s.index(mark):]
assert s.count(mark) == 1
s = s.replace(mark, new + mark)
old = '''         "slam": slam, "slam_armed": lambda name, rig: slam(name, rig, armed=True),'''
if '"kneel_aim"' not in s:
    assert s.count(old) == 1
    s = s.replace(old, old + '''\n         "kneel_aim": kneel_aim, "kneel_shot": kneel_shot,''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
