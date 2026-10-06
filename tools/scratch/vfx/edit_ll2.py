p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\shaders\loot_beam.gdshader"
s = open(p, encoding="utf-8").read()
reps = [
    # Rare: a deeper line, more of the ground taken under it (by day it read as a pale smudge).
    ("light = (tint * g(x, 0.026) * 1.0 + deep * g(x, 0.13) * 0.45) * fade * shimmer + deep * pool(half_w * 0.6) * 0.32;\n\t\tveil = (g(x, 0.05) * 0.3 + g(x, 0.16) * 0.12) * fade + pool(half_w * 0.6) * 0.1;",
     "light = (mix(tint, deep, 0.35) * g(x, 0.026) * 1.1 + deep * g(x, 0.13) * 0.5) * fade * shimmer + deep * pool(half_w * 0.6) * 0.34;\n\t\tveil = (g(x, 0.05) * 0.45 + g(x, 0.16) * 0.2) * fade + pool(half_w * 0.6) * 0.16;"),
    ("veil = (g(x, 0.045) * 0.32 + g(x, 0.14) * 0.12) * fade + pool(half_w * 0.6) * 0.1;",
     "veil = (g(x, 0.045) * 0.45 + g(x, 0.14) * 0.2) * fade + pool(half_w * 0.6) * 0.15;"),
    ("light = (tint * lines * 1.15 + deep * (halo * 0.32 + g(x, 0.26) * 0.1)) * fade + deep * pool(half_w * 0.6) * 0.32;\n\t\tveil = (g(x - s1, 0.045) + g(x + s1, 0.045)) * fade * 0.16 + pool(half_w * 0.6) * 0.1;",
     "light = (mix(tint, deep, 0.3) * lines * 1.2 + deep * (halo * 0.36 + g(x, 0.26) * 0.1)) * fade + deep * pool(half_w * 0.6) * 0.32;\n\t\tveil = (g(x - s1, 0.045) + g(x + s1, 0.045)) * fade * 0.26 + pool(half_w * 0.6) * 0.15;"),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
