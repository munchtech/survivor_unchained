from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\arts.py")
t = p.read_text(encoding="utf-8")
i = t.index("def chain_strike(")
j = t.index("ALL = (", i)
body = t[i:j]
E = [
    ('        (5, body({"hips": {"pos": (0.0, -0.34, 0.10)},', '        (6, body({"hips": {"pos": (0.0, -0.34, 0.10)},'),
    ('        (14, body({"hips": {"pos": (0.0, -0.18, 0.04)},', '        (15, body({"hips": {"pos": (0.0, -0.18, 0.04)},'),
    ('        (26, AXE_GUARD, "ease"),', '        (27, AXE_GUARD, "ease"),'),
    ('meta={"layer": "full", "contact": 2 / 30, "weapon": "axe",', 'meta={"layer": "full", "contact": 3 / 30, "weapon": "axe",'),
]
for a, b in E:
    assert body.count(a) == 1, a
    body = body.replace(a, b)
t = t[:i] + body + t[j:]
p.write_text(t, encoding="utf-8")
print("ok")
