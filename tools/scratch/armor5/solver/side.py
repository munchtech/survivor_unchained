import sys, numpy as np
SP = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8d13e5f-b1a5-4365-9d36-63505c60b8a1/scratchpad/"
z = np.load(SP + sys.argv[1]); D, L = z["D"], z["L"]; lo, h = z["lo"], float(z["h"])
side = sys.argv[2]  # l (+x) or r
y0, y1, z0, z1 = [float(v) for v in sys.argv[3].split(",")]
arm_any = ((D > 0) & L).any(0); body_any = ((D > 0) & ~L).any(0)
nx = D.shape[1]; c = (nx - 1) // 2
order = range(c, nx) if side == "l" else range(c, -1, -1)
print("per (y row, z col): cm of body-any extent from centre / free channel width cm before arm ('-' none, '+' >9)")
zs = [k for k in range(D.shape[3]) if z0 <= lo[2] + k * h <= z1][::2]
print("z:    " + " ".join(f"{lo[2] + k * h:+.2f}"[1:] if lo[2]+k*h>=0 else f"{lo[2] + k * h:+.2f}"[:5] for k in zs))
for j in range(D.shape[2] - 1, -1, -2):
    y = lo[1] + j * h
    if not (y0 <= y <= y1): continue
    s = ""
    for k in zs:
        xb = None; xa = None
        for i in order:
            if body_any[i, j, k]: xb = i
        for i in order:
            if xb is not None and (i - xb) * (1 if side == "l" else -1) <= 0: continue
            if arm_any[i, j, k]: xa = i; break
        bx = abs(xb - c) if xb is not None else 0
        w = "-" if xa is None else ("+" if abs(xa - (xb if xb is not None else c)) > 9 else str(abs(xa - (xb if xb is not None else c)) - 1))
        s += f"{bx:3d}/{w} "
    print(f"{y:.2f} {s}")
