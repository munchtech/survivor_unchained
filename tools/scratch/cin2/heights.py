"""Print a zone's ground heights on a grid: python heights.py ZONE X0 X1 Z0 Z1 STEP"""
import json, struct, sys
import numpy as np
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot\data\zones"
zone = sys.argv[1]
x0, x1, z0, z1, st = map(float, sys.argv[2:7])
meta = json.load(open(f"{G}/{zone}/zone.json", encoding="utf-8"))
size, res = meta["size"], meta["res"]
h = np.fromfile(f"{G}/{zone}/heights.bin", dtype=np.float32).reshape(res, res)
half, step = size / 2, size / (res - 1)


def at(x, z):
    fx = min(max((x + half) / step, 0), res - 1.0001); fz = min(max((z + half) / step, 0), res - 1.0001)
    i, j = int(fx), int(fz); tx, tz = fx - i, fz - j
    a, b, c, d = h[j, i], h[j, i + 1], h[j + 1, i], h[j + 1, i + 1]
    return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz


xs = np.arange(x0, x1 + 1e-6, st)
print("z\\x   " + " ".join(f"{x:6.0f}" for x in xs))
z = z0
while z <= z1 + 1e-6:
    print(f"{z:6.0f} " + " ".join(f"{at(x, z):6.2f}" for x in xs))
    z += st
