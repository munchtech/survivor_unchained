"""Mean arm cycle of 100STYLE Neutral_FR (left and right arms), phase-binned from hand fore-aft maxima."""
import sys, numpy as np
sys.path.insert(0, r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af8dbda3195e438e4/tools/anim")
import bvh
from armmetrics import unit, ang
b = bvh.load(r"C:/Users/munch/Tools/mocap/100STYLE/Neutral/Neutral_FR.bvh"); _, gp = b.globals(); n = b.names.index
hp = gp[:, n("Hips")]; v = np.linalg.norm(np.diff(hp[:, [0, 2]], axis=0), axis=1) * b.fps; v = np.append(v, v[-1])
lat = unit(gp[:, n("LeftShoulder")] - gp[:, n("RightShoulder")]); up0 = gp[:, n("Neck")] - gp[:, n("Chest")]
up = unit(up0 - lat * np.sum(up0 * lat, -1, keepdims=True)); fwd = np.cross(lat, up); mid = gp[:, n("Chest3")]
NB = 10
for side, sg, P in (("l", 1, "Left"), ("r", -1, "Right")):
    S, E, H = gp[:, n(P + "Shoulder")], gp[:, n(P + "Elbow")], gp[:, n(P + "Wrist")]
    L = np.mean(np.linalg.norm(E - S, axis=-1) + np.linalg.norm(H - E, axis=-1))
    lo = lat * sg; u = unit(E - S)
    th = np.degrees(np.arctan2(np.sum(u * fwd, -1), -np.sum(u * up, -1)))
    ab = np.degrees(np.arcsin(np.clip(np.sum(u * lo, -1), -1, 1)))
    el = ang(S - E, H - E)
    hf = np.sum((H - S) * fwd, -1) / L; hh = np.sum((H - S) * up, -1) / L; hx = np.sum((H - S) * lo, -1) / L
    # forward maxima while running fast
    pk = [i for i in range(5, len(hf) - 5) if hf[i] == hf[i - 5:i + 6].max() and v[i] > 130]
    acc = np.zeros((NB, 6)); cnt = np.zeros(NB)
    for a, c in zip(pk[:-1], pk[1:]):
        if not (25 < c - a < 60): continue
        for i in range(a, c):
            bi = int((i - a) / (c - a) * NB)
            acc[bi] += [th[i], el[i], ab[i], hf[i], hh[i], hx[i]]; cnt[bi] += 1
    m = acc / cnt[:, None]
    print(f"{side}: cycles {len(pk)-1}, L {L:.1f} cm, speed ~{np.median(v[pk]):.0f} cm/s, cycle frames median {np.median(np.diff(pk)):.0f}")
    print("  ph   theta  elbow  abd   handFwd/L handH/L handX/L")
    for i in range(NB):
        print(f"  {i/NB:.1f} {m[i,0]:6.1f} {m[i,1]:6.1f} {m[i,2]:5.1f}   {m[i,3]:+.2f}    {m[i,4]:+.2f}   {m[i,5]:+.2f}")
