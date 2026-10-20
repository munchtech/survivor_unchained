"""The viking_axe in its haft's own frame: t' along the haft (mm from the old grip point), radial (e1 the head's plane, e2 across)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools" / "assets"))
import grip_conform as gc

def haft_frame(pc):
    t0, t1 = pc.band(gc.piece_cfg(gc.spec(), pc.row, pc.id))
    m, cl, e1, e2, t, R = pc.frame(t0, t1)
    ts = np.linspace(-80, 150, 24)
    C = np.array([pc.G + cl(np.array([x]))[0] + pc.D * (x / pc.mm) for x in ts])
    c0 = C.mean(0); w, v = np.linalg.eigh(np.cov((C - c0).T)); d = v[:, -1]
    if d @ pc.D < 0: d = -d
    O = c0 + d * ((pc.G - c0) @ d)          # the haft line's point nearest the old grip point
    a1 = e1 - d * (e1 @ d); a1 /= np.linalg.norm(a1); a2 = np.cross(d, a1)
    return O, d, a1, a2

def coords(pc, O, d, a1, a2, P=None):
    P = pc.P if P is None else P
    Q = P - O; tt = Q @ d * pc.mm; u = Q @ a1 * pc.mm; v = Q @ a2 * pc.mm
    return tt, u, v

def long_tris(pc, span=100.0):
    node, p, M = pc.parts[0]
    a = pc.g.js["accessors"][p["indices"]]; bv = pc.g.js["bufferViews"][a["bufferView"]]
    off = pc.g.bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    I = np.frombuffer(bytes(pc.g.b[off:off + a["count"] * 4]), "<u4").reshape(-1, 3)
    t = (pc.P - pc.G) @ pc.D * pc.mm
    return I, I[(t[I].max(1) - t[I].min(1)) > span]

if __name__ == "__main__":
    pc = gc.load("viking_axe")
    O, d, a1, a2 = haft_frame(pc)
    print("O off G mm", np.linalg.norm(O - pc.G) * pc.mm)
    tt, u, v = coords(pc, O, d, a1, a2)
    I, L = long_tris(pc)
    pv = np.unique(L)
    for nm, sel in (("butt ring", pv[tt[pv] < 0]), ("top ring", pv[tt[pv] > 0])):
        print(nm, len(sel), f"t {tt[sel].min():.1f}..{tt[sel].max():.1f} u {u[sel].min():.1f}..{u[sel].max():.1f} v {v[sel].min():.1f}..{v[sel].max():.1f}")
    r = np.hypot(u, v)
    for a in range(-130, 700, 10):
        s = (tt >= a) & (tt < a + 10) & (r < 45)
        if s.sum(): print(f"{a:5d} n{s.sum():4d} u {u[s].min():6.1f}..{u[s].max():6.1f} v {v[s].min():6.1f}..{v[s].max():6.1f}")
