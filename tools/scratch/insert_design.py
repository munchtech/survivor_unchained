p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\docs\SKILLS_DESIGN.md"
sp = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
s = open(p, encoding="utf-8").read()
d165 = open(sp + r"\design_165.md", encoding="utf-8").read().rstrip() + "\n\n"
d17 = open(sp + r"\design_17.md", encoding="utf-8").read().rstrip() + "\n\n---\n\n"
a = "### 16.5 Decisions the studies left open"
assert s.count(a) == 1
s = s.replace(a, d165 + "### 16.8 Decisions the studies left open")
b = "## 17. Before and after"
assert s.count(b) == 1
s = s.replace(b, d17 + "## 18. Before and after")
c = "## 18. Open"
assert s.count(c) == 1
s = s.replace(c, "## 19. Open")
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
