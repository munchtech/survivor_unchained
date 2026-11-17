"""elbow.py SHOTDIR NLEGS: the right elbow's inside angle (deg) from the skeleton (BODY2 points 7 upperarm_r, 9 hand_r, 13 lowerarm_r; angle at lowerarm_r
between upperarm_r and hand_r). Per leg the max and mean over the stand (+44..+59 of the leg, which holds the next leg's -10..-1, frames where the log's
mov is 0) and the frames over 150 (a locked-straight elbow)."""
import sys, math
LIM = 150.0
def load(d):
    R = {}; fi = -1; mov = {}
    for ln in open(d + "/views.log", errors="ignore"):
        if ln.startswith("SCR2 "): fi += 1
        elif ln.startswith("BODY2 ") and fi >= 0:
            t = ln.split(); v = [float(x) for x in t[1:46]]
            if len(v) < 45: continue
            P = lambda i: v[3 * i:3 * i + 3]
            R[fi] = (P(7), P(9), P(13))
        elif ln.startswith("BLADE ") and fi >= 0 and " sv " in ln:
            t = ln.split(); mov[fi] = float(t[t.index("sv") + 4])
    return R, mov
def ang(u, h, e):
    a = [u[i] - e[i] for i in range(3)]; b = [h[i] - e[i] for i in range(3)]
    d = sum(x * y for x, y in zip(a, b)); n = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    return math.degrees(math.acos(max(-1, min(1, d / n)))) if n else float("nan")
if __name__ == "__main__":
    R, mov = load(sys.argv[1]); n = int(sys.argv[2])
    for L in range(n):
        s = 60 + 60 * L
        fr = [(k - s, ang(*R[k])) for k in range(s + 44, s + 60) if k in R and mov.get(k, 0) == 0]
        if not fr: print(f"L{L}: no stand frames"); continue
        a = [x for _, x in fr]; over = [f"{k:+d}:{x:.0f}" for k, x in fr if x > LIM]
        print(f"L{L}: elbow max {max(a):.0f} mean {sum(a) / len(a):.0f} over {len(a)} stand frames" + (f"; > {LIM:.0f}: " + " ".join(over) if over else ""))
