"""python diff.py TAGA TAGB SHOT [x0,y0,x1,y1]: mean luma difference (B - A) and mean |B - A| in a box, three faces"""
import sys
import numpy as np
from PIL import Image
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots" + "\\"
a, b, shot = sys.argv[1:4]
box = tuple(int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else "700,150,1150,650").split(","))
L = lambda p: (np.asarray(Image.open(p).convert("RGB").crop(box)).astype(float) @ [0.2126, 0.7152, 0.0722])
for f in ("own", "saffron", "sunborn"):
    try: A, B = L(f"{SH}f30c{a}_{f}_{shot}.png"), L(f"{SH}f30c{b}_{f}_{shot}.png")
    except FileNotFoundError: continue
    print(f"{shot} {f:8s} mean {(B - A).mean():+6.2f}  |d| {np.abs(B - A).mean():5.2f}  p99|d| {np.percentile(np.abs(B - A), 99):5.1f}")
