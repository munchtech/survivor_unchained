import sys, numpy as np
SP = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8d13e5f-b1a5-4365-9d36-63505c60b8a1/scratchpad/"
z = np.load(SP + sys.argv[1]); D, L, F = z["D"], z["L"], list(z["F"]); lo, h = z["lo"], float(z["h"])
i0 = F.index("idle_warden_town@0")
arm_any = ((D > 0) & L).any(0); body_any = ((D > 0) & ~L).any(0); rest0 = D[i0] > 0
xs = sys.argv[3].split(",") if len(sys.argv) > 3 else None
for y in [float(v) for v in sys.argv[2].split(",")]:
    j = int(round((y - lo[1]) / h))
    print(f"y={y}  rows: z from front (top) to back; cols: x from her right (left) to her left (right)")
    for k in range(D.shape[3] - 1, -1, -2):
        s = ""
        for i in range(0, D.shape[1]):
            s += "#" if rest0[i, j, k] else "a" if arm_any[i, j, k] else "b" if body_any[i, j, k] else "."
        print(f"{lo[2] + k * h:+.2f} {s}")
