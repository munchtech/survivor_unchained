import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('tools/assets/heroine_paint.py', [
    # (the game's tone mapping, AgX, turns a pure blue toward violet and a deep red toward rust:
    # so the woad leans to cyan and the blood to crimson, to be seen as blue and as blood)
    ("    blue = hexc('#0c48b4')", "    # (toward cyan: the game's tone mapping turns a pure blue violet)\n    blue = hexc('#0a62c4')"),
    ("        lay(L, c, hexc('#640510'), 0.97,", "        # (toward crimson: the game's tone mapping turns a deep red to rust)\n        lay(L, c, hexc('#6c0322'), 0.97,"),
    ("    red = hexc('#922a10')", "    red = hexc('#8a1e0e')"),
    ("        x0, y0 = xs.mean() - out * 60, ys.max() + 70", "        x0, y0 = xs.mean() - out * 20, ys.max() + 92"),
    ("        line = spline([(x0, y0), (x0 + out * 90, y0 + 14), (x0 + out * 200, y0 - 6), (x0 + out * 290, y0 - 60)], 200)",
     "        line = spline([(x0, y0), (x0 + out * 80, y0 + 8), (x0 + out * 180, y0 - 14), (x0 + out * 260, y0 - 70)], 200)"),
    ("        for i in range(70):", "        for i in range(46):"),
    ("            wide = 26 + 30 * np.sin(np.pi * t)", "            wide = 14 + 18 * np.sin(np.pi * t)"),
    ("            spots.append((px + rng.normal(0, 8), py + rng.normal(0, wide * 0.35), (14 + 26 * np.sin(np.pi * t)) * rng.uniform(0.6, 1.1)))",
     "            spots.append((px + rng.normal(0, 6), py + rng.normal(0, wide * 0.3), (10 + 18 * np.sin(np.pi * t)) * rng.uniform(0.6, 1.1)))"),
])
