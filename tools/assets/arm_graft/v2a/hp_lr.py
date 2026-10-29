# Body 2 A: on exported glbs (orig + mine): (1) the arm paint's fine detail (d_b's cylindrical unwrap, every material;
# high-pass rms of luminance, sigma HP_SIG px at 0.15 cm x 1 deg per px, z 3-48 cm), (2) left vs right: the same pose
# mirrored onto each arm (d_c b.py's mirrorG), R points to the mirrored L surface, per region mean/p95/max mm,
# (3) swell: bone-local radius change vs rest on the right arm (upper/elbow/forearm), mean / p95 mm.
#   python hp_lr.py <mine glb> [orig glb]
import os, sys, numpy as np
B = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\23290ad1-ed63-4a0d-8e12-ac0911d16c27\scratchpad\body2"
sys.path.insert(0, B + r"\d_b"); sys.path.insert(0, B + r"\d_c")
import cm
from raster import raster, sample
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
import m as dcm
MINE = sys.argv[1]; cm.FILES["mine"] = MINE
if len(sys.argv) > 2: cm.FILES["orig"] = sys.argv[2]
ZS = 0.15; SIG = float(os.environ.get("HP_SIG", "4"))
MX = np.diag([-1., 1, 1, 1])
def mirrorG(b, G):
    sw = [b.sk.index.get(n[:-2] + ("_l" if n.endswith("_r") else "_r"), i) if n[-2:] in ("_l", "_r") else i for i, n in enumerate(b.sk.names)]
    out = np.empty_like(G)
    for j in range(len(G)): out[sw[j]] = MX @ G[j] @ b.rest_inv[j] @ MX @ b.rest[sw[j]]
    return out
def unwrap(b, s):
    z, phi, rad, seg, ok, segs = cm.armcoords(b, s); T = b.T[ok[b.T].all(1)]; col = None
    for mi in sorted(set(b.MI.tolist())):
        Tm = T[b.MI[T[:, 0]] == mi]
        if not len(Tm): continue
        Xc = phi[Tm].copy(); span = Xc.max(1) - Xc.min(1); wrap = span > 180; Xc[wrap] = np.where(Xc[wrap] < 0, Xc[wrap] + 360, Xc[wrap])
        idx = np.arange(Tm.size).reshape(-1, 3); A = b.UV[Tm.ravel()]
        img = raster(Xc.ravel() + 180, (z[Tm] / ZS).ravel(), idx, A, 540, int(52 / ZS) + 1)
        img[:, :180] = np.where(np.isnan(img[:, :180]), img[:, 360:540], img[:, :180]); img = img[:, :360]
        mk = ~np.isnan(img[..., 0])
        if col is None: col = np.full(img.shape[:2] + (3,), np.nan, np.float32)
        col[mk] = sample(b.imgs[mi], img[mk][:, :2])
    return col
def hp(col):
    L = col @ np.array([0.299, 0.587, 0.114]); m = ~np.isnan(L); L0 = np.where(m, L, 0)
    num = gaussian_filter(L0, SIG); den = gaussian_filter(m.astype(float), SIG); lo = num / np.maximum(den, 1e-6)
    zz = np.arange(L.shape[0]) * ZS; band = ((zz > 3) & (zz < 48))[:, None] & m & (den > 0.9)
    return float(np.sqrt(np.mean((L - lo)[band] ** 2))), float(np.std(lo[band]))
bodies = {t: cm.load(t) for t in ("orig", "mine")}
for t, b in bodies.items():
    print("HP", t, " ".join("%s %.4f (low std %.4f)" % ((s,) + hp(unwrap(b, s))) for s in "rl"))
# --- L/R and swell
for t, b in bodies.items():
    I = b.sk.index; ci = b.clip("idle_reaver_town"); cs = b.clip("reaver_show")
    poses = {"rest": b.rest, "idle": b.globals(ci, 0), "A58": b.globals(cs, 18), "A82": b.globals(cs, 24), "show.77": b.globals(cs, 23)}
    for pn, G in poses.items():
        Pr = b.P if pn == "rest" else b.pose(G); Pl = b.P if pn == "rest" else b.pose(mirrorG(b, G))
        Prw, T, wid = dcm.weldmesh(b, Pr); Plw, _, _ = dcm.weldmesh(b, Pl)
        Lm = Plw * np.array([-1, 1, 1.]); keepT = T[(Lm[T][:, :, 0] < -0.07).all(1)]
        samp = dcm.sample_tris(Lm, keepT[:, ::-1]); tr = cKDTree(samp)
        H, E, Hd = dcm.frame(G, I, "r"); ac = dcm.armcoords(Prw, H, E, Hd, "r"); rg = dcm.regions(ac); side = Prw[:, 0] < 0
        line = "LR %s %-7s" % (t, pn)
        for k in ("deltoid", "pit", "upper", "elbow", "forearm", "wrist"):
            d, _ = tr.query(Prw[rg[k] & side]); line += " %s %.1f/%.1f/%.1f" % (k, d.mean() * 1e3, np.percentile(d, 95) * 1e3, d.max() * 1e3)
        print(line)
    # swell: right arm, bone-local radius vs rest
    z, phi, rad, seg, ok, segs = cm.armcoords(b, "r"); Lu = np.linalg.norm(segs[0][1] - segs[0][0]) * 100
    for pn in ("idle", "A58", "A82", "show.77"):
        G = poses[pn]; Pp = b.pose(G); S = b.skin_mats(G); line = "SWELL %s %-7s" % (t, pn)
        for k, bn, z0, z1 in (("upper", "upperarm_r", 9, Lu - 3), ("elbow", "lowerarm_r", Lu - 2, Lu + 4), ("forearm", "lowerarm_r", Lu + 4, Lu + 22)):
            M = np.linalg.inv(S[I[bn]]); Pl_ = (M[:3, :3] @ Pp.T).T + M[:3, 3]
            z2, phi2, rad2, seg2, _, _ = cm.armcoords(b, "r", P=Pl_)
            mm = ok & (z >= z0) & (z < z1) & ~np.isnan(rad2); d = (rad2[mm] - rad[mm]) * 10
            line += " %s %+.1f/%.1f" % (k, d.mean(), np.percentile(np.abs(d), 95))
        print(line)
