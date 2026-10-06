p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_build.py"
s = open(p, encoding="utf-8").read()
a = s.index("def stage_form():")
b = s.index("def smoothstep(")
new = open(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\boar\new_form2.py", encoding="utf-8").read()
s = s[:a] + new + s[b:]
open(p, "w", encoding="utf-8").write(s)
c = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_config.py"
t = open(c, encoding="utf-8").read()
t = t.replace('''        "tusks": (-0.58, 0.06, 0.40, 0.62),           # forward of y, outside |x|, between z''',
              '''        "tusks": (-0.74, -0.55, 0.095, 0.33, 0.62),   # between y, outside |x|, between z''')
open(c, "w", encoding="utf-8").write(t)
print("ok")
