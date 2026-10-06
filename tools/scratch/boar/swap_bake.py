p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_build.py"
s = open(p, encoding="utf-8").read()
a = s.index("def stage_bake():")
b = s.index("STAGES = {")
new = open(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\boar\new_bake.py", encoding="utf-8").read()
s = s[:a] + new + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
