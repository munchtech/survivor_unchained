# g2c extra numbers on an export: forearm outline (A82 and idle) and the seam ring ratios (elbow, wrist), both sides.
#   python extra.py <people dir>
import os, sys
os.environ["ANIM_PEOPLE"] = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "g2a"))
import numpy as np
from g2lib import *
from skin import Body
from common import regions, armframe
import meas
b = Body.heroine(jiggle=False, head=True, helpers=True); meas.prep(b); I = b.sk.index
cl = b.clip("reaver_show"); ci = b.clip("idle_reaver_town")
Pr = meas.weld(b, b.P)
for s in "rl":
    reg, info = regions(b, s)
    fa = meas.wmask(b, reg["forearm"])
    line = f"[{s}]"
    for pn, G in (("A82", b.globals(cl, 24)), ("idle", b.globals(ci, 0))):
        mir = s == "l" and pn == "A82"
        if mir: G = meas.mirrorG(b, G)
        Pw = meas.weld(b, b.pose(G)); n, a = meas.fn(b, Pw)
        o = meas.silhouette(b, Pw, n, fa, mir)
        if o:
            c = o["chain"]; sg = np.diff(c, axis=0); Lc = np.linalg.norm(sg, axis=1); sg = sg[Lc > 0.5]; Lc = Lc[Lc > 0.5]
            ang = np.degrees(np.arccos(np.clip((sg[1:] * sg[:-1]).sum(1) / Lc[1:] / Lc[:-1], -1, 1)))
            line += f" forearm {pn} chain {Lc.sum():.0f}px chord {np.median(Lc):.1f}/{np.percentile(Lc,90):.1f}px corner {np.median(ang):.0f}/{np.percentile(ang,90):.0f}d"
        else:
            line += f" forearm {pn} -"
    # inner elbow at A82 (bend ~112): faces losing over half their area, by count and by rest area
    G = b.globals(cl, 24); G = meas.mirrorG(b, G) if s == "l" else G
    Pw = meas.weld(b, b.pose(G)); n, a = meas.fn(b, Pw); n0, a0 = meas.fn(b, Pr)
    ie = meas.wmask(b, reg["inner_elbow"]); t_ = ie[b.Tw].all(1); col = (a[t_] / np.maximum(a0[t_], 1e-12)) < 0.5
    line += f" | inner elbow <0.5: {col.mean():.0%} of faces, {a0[t_][col].sum()/a0[t_].sum():.0%} of area"
    # ring ratios: median skin edge length per 1 cm band along the arm (rest), the biggest neighbour-band step
    H, E, Hd, u, L, up, fr = armframe(b, s)
    sk = (b.piece == "Heroine"); side = (b.P[:, 0] < 0) if s == "r" else (b.P[:, 0] > 0)
    EP = b.EP; M = Pr[EP].mean(1); el = np.linalg.norm(Pr[EP[:, 0]] - Pr[EP[:, 1]], axis=1)
    hb = np.zeros(b.nW, bool); hb[b.wid[sk & side]] = True; ok = hb[EP].all(1)
    for nm_, A0, ax, Lb in (("elbow", E, (E - H) / np.linalg.norm(E - H), 0.0), ("wrist", Hd, (Hd - E) / np.linalg.norm(Hd - E), 0.0)):
        d = (M - A0) @ ax; rr = np.linalg.norm((M - A0) - np.outer(d, ax), axis=1)
        med = []
        for c in np.arange(-0.06, 0.061, 0.01):
            m = ok & (d >= c) & (d < c + 0.01) & (rr < 0.07)
            med.append(np.median(el[m]) * 100 if m.sum() > 5 else np.nan)
        med = np.array(med); st = np.nanmax(np.maximum(med[1:] / med[:-1], med[:-1] / med[1:]))
        line += f" | {nm_} bands(cm) " + " ".join(f"{x:.2f}" for x in med) + f" max step {st:.2f}x"
    print(line)
