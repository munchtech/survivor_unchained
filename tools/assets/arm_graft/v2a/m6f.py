# Body 2 A: d_b m6's weight swap on "mine" (fake or MINE_GLB): pit shear (helix turn vs rest, z 1-7/7-13/13-19/19-23)
# with mine's own weights vs her post-split weights IDW'd (k=4) onto mine's arm.
import os, sys, numpy as np
B = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\23290ad1-ed63-4a0d-8e12-ac0911d16c27\scratchpad\body2"
sys.path.insert(0, B + r"\d_b"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm, geo
from skin import Body
from scipy.spatial import cKDTree
_real = Body.heroine
if os.environ.get("FAKE_DUMP"): import fake
o = _real(jiggle=False, helpers=True, body_file=cm.FILES["orig"])
g = _real(jiggle=False, helpers=True, body_file=os.environ["MINE_GLB"]) if os.environ.get("MINE_GLB") else Body.heroine(jiggle=False, helpers=True)
def dense(b):
    D = np.zeros((len(b.P), len(b.sk.names)))
    for k in range(4): np.add.at(D, (np.arange(len(b.P)), b.J[:, k]), b.W[:, k])
    return D
Do = dense(o); Dg = dense(g); I = g.sk.index
z, phi, rad, seg, ok, segs = cm.armcoords(g, "r"); _, _, _, _, oko, _ = cm.armcoords(o, "r")
tr = cKDTree(o.P[oko]); dd, ii = tr.query(g.P[ok], k=4); w = 1 / np.maximum(dd, 1e-5); w /= w.sum(1, keepdims=True)
Dn = Dg.copy(); Dn[ok] = (Do[oko][ii] * w[..., None]).sum(1)
zb = [(1, 7), (7, 13), (13, 19), (19, 23)]; h0 = geo.helix(geo.edge_stats(g, "r"), zb)
rs = g.clip("reaver_show")
for lab, DD in (("own", Dg), ("her IDW", Dn)):
    order = np.argsort(-DD, 1)[:, :4]; g.J = order; g.W = np.take_along_axis(DD, order, 1); g.W /= g.W.sum(1, keepdims=True)
    for f in (23, 24):
        G = g.globals(rs, f); h = geo.helix(geo.edge_stats(g, "r", P=g.pose(G), R=G), zb)
        print(lab, "f", f, "turn vs rest d/cm " + " ".join(f"{x[4]-y[4]:+.2f}" for x, y in zip(h, h0)))
BN = ["clavicle", "upperarm", "upperarm_twist_01", "upperarm_share", "spine_03"]
for z0 in (0, 4, 8):
    m = ok.copy(); m[ok] = (z[ok] >= z0) & (z[ok] < z0 + 4)
    print("z%d-%d" % (z0, z0 + 4), "own", " ".join(f"{Dg[m, I[n + ('_r' if n != 'spine_03' else '')]].mean():.2f}" for n in BN), "| IDW", " ".join(f"{Dn[m, I[n + ('_r' if n != 'spine_03' else '')]].mean():.2f}" for n in BN))
# (experiments) which part of the IDW matters
iu, it, ic, ish = I["upperarm_r"], I["upperarm_twist_01_r"], I["clavicle_r"], I["upperarm_share_r"]
fo = np.where(Dg[:, iu] + Dg[:, it] > 1e-9, Dg[:, it] / np.maximum(Dg[:, iu] + Dg[:, it], 1e-9), 0)
D3 = Dn.copy(); Up = Dn[:, iu] + Dn[:, it]; D3[:, it] = Up * fo; D3[:, iu] = Up * (1 - fo)
D4 = Dg.copy(); fn = np.where(Dn[:, iu] + Dn[:, it] > 1e-9, Dn[:, it] / np.maximum(Dn[:, iu] + Dn[:, it], 1e-9), 0); Up = Dg[:, iu] + Dg[:, it]; D4[:, it] = Up * fn; D4[:, iu] = Up * (1 - fn)
for lab, DD in (("IDW, twist frac own", D3), ("own, twist frac IDW", D4)):
    order = np.argsort(-DD, 1)[:, :4]; g.J = order; g.W = np.take_along_axis(DD, order, 1); g.W /= g.W.sum(1, keepdims=True)
    G = g.globals(rs, 24); h = geo.helix(geo.edge_stats(g, "r", P=g.pose(G), R=G), zb)
    print(lab, "f24 turn vs rest d/cm " + " ".join(f"{x[4]-y[4]:+.2f}" for x, y in zip(h, h0)))
import importlib.util as _iu
_sp = _iu.spec_from_file_location("ageo", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "geo.py")); _ag = _iu.module_from_spec(_sp); _sp.loader.exec_module(_ag); Surf = _ag.Surf
To = o.T[(o.piece[o.T] == "Heroine").all(1)] if hasattr(o, "piece") else o.T
Sf = Surf(o.P, To); q_, dist_, fi_, bar_ = Sf.query(g.P[ok])
D5 = Dg.copy(); D5[ok] = (Do[To[fi_]] * bar_[:, :, None]).sum(1)
print("bary dist mm p50 %.2f p95 %.2f" % (np.median(dist_) * 1e3, np.percentile(dist_, 95) * 1e3))
for lab, DD in (("her post-split BARY", D5),):
    order = np.argsort(-DD, 1)[:, :4]; g.J = order; g.W = np.take_along_axis(DD, order, 1); g.W /= g.W.sum(1, keepdims=True)
    G = g.globals(rs, 24); h = geo.helix(geo.edge_stats(g, "r", P=g.pose(G), R=G), zb)
    print(lab, "f24 turn vs rest d/cm " + " ".join(f"{x[4]-y[4]:+.2f}" for x, y in zip(h, h0)))
