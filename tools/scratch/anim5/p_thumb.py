from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\keyed.py")
t = p.read_text(encoding="utf-8")
E = [
    ('in ("blade", "knuckles", "pole") and all(f"{n[:-2]}#{i}"', 'in ("blade", "knuckles", "pole", "thumb") and all(f"{n[:-2]}#{i}"'),
    ('aimed = [isinstance(k[1].get(h), dict) and ("blade" in k[1][h] or "knuckles" in k[1][h]) for k in keys]',
     'aimed = [isinstance(k[1].get(h), dict) and any(v in k[1][h] for v in ("blade", "knuckles", "thumb")) for k in keys]'),
    ('and any(v in k[1][h] for v in ("blade", "knuckles", "pole"))}', 'and any(v in k[1][h] for v in ("blade", "knuckles", "pole", "thumb"))}'),
    ('            for v in ("blade", "knuckles", "pole"):', '            for v in ("blade", "knuckles", "pole", "thumb"):'),
]
for a, b in E:
    assert t.count(a) == 1, a
    t = t.replace(a, b)
# The docstring: the new control.
a = '''               "pole": (x, y, z) the way the elbow points,'''
b = '''               "pole": (x, y, z) the way the elbow points,
               "thumb": (x, y, z) instead of blade and knuckles: the wrist
                      left straight, the forearm rolled so the thumb side
                      faces as near this way as it can (a carried weapon),'''
assert t.count(a) == 1
t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
