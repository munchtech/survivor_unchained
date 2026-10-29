"""The reaver's hung axe (HipLoop row) as candidate rows (Body 17): hang.py's measure with the game's hang constants
(SheathHang: Keep 0.2, Lag 0.2, Settle 1.5), the swing computed once per clip and every row measured on the same posed
frames. A row: pivot (the haft's top on the belt, skeleton rest space, her right side), the shaft's rest lean `out`
(deg, foot away from her leg) and `fore` (deg, + foot forward); the basis is the old row's turned by the least turn onto
the new shaft; At = pivot - 0.56 * shaft (the pivot is the mount's (0, 0.56, 0)).
usage: python row.py [--step=2] [--clips=walk,...] [--frog] ROW...   ROW = px,py,pz,out,fore  ('old' = the current row)"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scratch" / "body16"))
argv = sys.argv[1:]
sys.argv = [sys.argv[0], "--fast", "--clips=none"]
import hang as h
ac = h.ac
opt = dict((a[2:].split("=", 1) + [""])[:2] for a in argv if a.startswith("--"))
rows_in = [a for a in argv if not a.startswith("--")] or ["old"]
STEP = int(opt.get("step", 1))
K, TAU, TS = 0.2, 0.2, 1.5
S0 = np.array([0.319, 0.925, 0.205]); S0 /= np.linalg.norm(S0)
T0 = np.array([0.945, -0.326, 0.0]); T0 = T0 - S0 * (T0 @ S0); T0 /= np.linalg.norm(T0)
N0 = np.array([-0.5, 0, -0.866])
P0 = np.array([-0.110, 1.06, -0.190])
YP = 0.56
REST = np.eye(4); REST[:3, :3] = h.rotx(20.6); REST[:3, 3] = (0, 1.0723, 0)
CLR = json.loads(ac.CLEARANCE.read_text())["reaver"]["hip_loop"]


def turn(a, b):
    v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    k = v / s; K_ = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    th = math.atan2(s, c)
    return np.eye(3) + math.sin(th) * K_ + (1 - math.cos(th)) * K_ @ K_


def parse(r):
    if r == "old":
        return P0, S0
    px, py, pz, out, fore = map(float, r.split(","))
    # the shaft's foot (down) in her rest frame: x = -sin(out) (out = away from her right leg: -X), z = sin(fore)
    d = np.array([-math.tan(math.radians(out)), -1, math.tan(math.radians(fore))]); d /= np.linalg.norm(d)
    return np.array([px, py, pz]), -d


def mount(P, s, left):
    t = turn(S0, s) @ T0; n = N0.copy(); P = P.copy(); s = s.copy()
    if left:
        P[0] = -P[0]; s[0] = -s[0]; t[0] = -t[0]; n[0] = -n[0]; t = -t
    at = P - YP * s + n * CLR; P = P + n * CLR
    third = np.cross(s, t)
    T = np.eye(4); T[:3, :3] = np.c_[third, s, t]; T[:3, 3] = at
    A = np.linalg.inv(REST) @ T
    return A, (np.linalg.inv(REST) @ np.r_[P, 1])[:3], t


KEYS = ["viking_axe@hand_r", "viking_axe@hand_l"]
raw = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"]
tmp = HERE / "_arms.json"; tmp.write_text(json.dumps({"sheathed": {k: raw[k] for k in KEYS}}))
ck = ac.SocketChecker("reaver", str(tmp))
b, I, vb = ck.b, ck.I, ck.vbone
d0 = ck.sheathed[KEYS[0]]; A0 = np.vstack([d0["mount"], [0, 0, 0, 1]])
PTS = (np.linalg.inv(A0) @ np.c_[ck.pts_s[KEYS[0]], np.ones(len(ck.pts_s[KEYS[0]]))].T).T[:, :3]   # mount space
FROG = "frog" in opt
if FROG:
    import frog, frog2
FING = ("index", "middle", "ring", "pinky", "thumb")
HAND = np.array([(n.startswith("hand") or n.split("_")[0] in FING) for n in vb])
Pr = h.rotx(20.6)
cands = [(r, *parse(r)) for r in rows_in]
names = ["idle", "walk", "run", "sprint"]
if "clips" in opt: names = opt["clips"].split(",")
for r, P, s in cands:
    print(f"row {r}: pivot {np.round(P,3).tolist()} shaft {np.round(s,3).tolist()} at {np.round(P - YP*s,3).tolist()} thick {np.round(turn(S0,s)@T0,3).tolist()}")
FP = {}
if FROG:
    G0 = b.frames(b.clip("idle_reaver_town"))[0]; P0_ = b.pose(G0); ck.body.pose(P0_); M0 = G0[I["pelvis"]]
    for ci, (r, P, s) in enumerate(cands):
        for left in (False, True):
            A, pl, t = mount(P, s, left)
            n = N0.copy(); s2 = s.copy()
            if left: n[0] = -n[0]; s2[0] = -s2[0]
            third = np.cross(s2, t); inward = np.array([third @ -n, 0, t @ -n]); inward /= np.linalg.norm(inward)
            top, u, v, back = frog.haft(PTS, inward)
            poll, cheek = frog2.haftpc(PTS, top, inward)
            st, fdir = frog2.ray_start(inward, poll, cheek)
            if "reach" in opt: reach = float(opt["reach"])
            else:
                ray = np.array([top + st + fdir * x for x in np.arange(0, 0.2, 0.001)])
                W = (M0[:3, :3] @ A[:3, :3] @ ray.T).T + M0[:3, :3] @ A[:3, 3] + M0[:3, 3]
                dd, nr = ck.body.signed(P0_, W, reach=0.14, k=8)
                inn = np.isfinite(dd) & (ck.cover[nr] - dd > 0)
                reach = float(np.argmax(inn) * 0.001) if inn.any() else 0.2
                cv = ck.cover[nr[np.argmax(inn)]] if inn.any() else -1
            pts = frog2.frog(u, v, inward, poll, cheek, reach); up = reach
            FP[(ci, left)] = pts + top
            print(f"frog {r} {'L' if left else 'R'}: poll {poll:.4f} cheek {cheek:.4f} cover@belt {cv*1000 if not 'reach' in opt else 0:.1f}mm top {np.round(top,4).tolist()} half {u:.4f} {v:.4f} inward {np.round(inward,3).tolist()} back {back:.4f} reach {reach:.3f} strap at {up:.4f}", flush=True)
res = {}
for nm in names:
    clip = b.clip(f"{nm}_reaver_town"); Gs = b.frames(clip); dt = 1.0 / clip.fps
    sw = None; os_ = []
    for p in range(2):
        for f in range(len(Gs)):
            M = Gs[f][I["pelvis"]]; R = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
            D = h.quat(R @ Pr.T)
            if sw is None: avg = o = D
            avg = h.slerp(avg, D, 1 - math.exp(-dt / TS)); tg = h.slerp(avg, D, K)
            o = h.slerp(o, tg, 1 - math.exp(-dt / TAU)); sw = o
            if p == 1: os_.append(D if nm in opt.get("rigid", "").split(",") else o)
    acc = {}
    for f in range(0, len(Gs), STEP):
        G = Gs[f]; M = G[I["pelvis"]]; Pp = b.pose(G); ck.body.pose(Pp)
        htree = cKDTree(Pp[HAND])
        for ci, (r, P, s) in enumerate(cands):
            for left in ((False,) if opt.get("side") == "R" else (True,) if opt.get("side") == "L" else (False, True)):
                A, pl, _ = mount(P, s, left)
                Rw = h.mat(os_[f]) @ Pr @ A[:3, :3]
                pw = M[:3, :3] @ pl + M[:3, 3]
                qm = np.linalg.inv(A) @ np.r_[pl, 1]
                org = pw - Rw @ qm[:3]
                y = Rw[:, 1]; v = y if y[1] < 0 else -y
                out_s = 1 if left else -1
                a_out = math.degrees(math.atan2(v[0] * out_s, -v[1])); a_fore = math.degrees(math.atan2(v[2], -v[1]))
                e = acc.setdefault((ci, left), dict(o=[], f=[], skin=-99.0, outfit=-99.0, hand=9.0, fs=0, fo=0, fskin=-99.0, foutfit=-99.0))
                e["o"].append(a_out); e["f"].append(a_fore)
                sets = [("", PTS)] + ([("f", FP[(ci, left)])] if FROG else [])
                for tag, pm in sets:
                    Q = pm @ Rw.T + org
                    keep, near, _ = ck.measure(Pp, ck.body, Q)
                    dd, nr = ck.body.signed(Pp, Q, reach=0.14, k=8)
                    ok = np.isfinite(dd) & (dd > -0.002)
                    od = np.full(len(Q), -99.0); od[ok] = (ck.cover[nr[ok]] - dd[ok]) * 1000.0
                    fin = np.isfinite(dd)
                    kv = max(float(keep.max()), float((-dd[fin] * 1000).max()) if fin.any() else -99.0)
                    keep = np.array([kv])
                    if tag == "":
                        if keep.max() > e["skin"]: e["skin"], e["fs"] = float(keep.max()), f
                        if od.max() > e["outfit"]:
                            j = int(od.argmax()); e["outfit"], e["fo"] = float(od.max()), f
                            e["wo"] = f"y{pm[j,1]:+.2f} {vb[nr[j]]}"
                        sk = -dd * 1000; sk[~fin] = -99
                        if sk.max() > e.get("sk", -99):
                            j = int(sk.argmax()); e["sk"] = float(sk.max()); e["ws"] = f"y{pm[j,1]:+.2f} {vb[nr[j]]} f{f}"
                        e["hand"] = min(e["hand"], float(htree.query(Q)[0].min()))
                        hm = (pm[:, 1] > 0.45) & fin & np.array([vb[k].startswith(("pelvis", "thigh", "spine")) for k in nr])
                        gs = float(dd[hm].min() * 1000) if hm.any() else 99.0
                        go = float((dd[hm] - ck.cover[nr[hm]]).min() * 1000) if hm.any() else 99.0
                        e.setdefault("gs", []).append(gs); e.setdefault("go", []).append(go)
                    else:
                        e["fskin"] = max(e["fskin"], float(keep.max())); e["foutfit"] = max(e["foutfit"], float(od.max()))
    for (ci, left), e in sorted(acc.items()):
        o, fo = np.array(e["o"]), np.array(e["f"])
        gs, go = np.array(e["gs"]), np.array(e["go"])
        if "compact" in opt:
            print(f"{nm:6} {cands[ci][0]:26} {'L' if left else 'R'} out {o.min():4.1f}..{o.max():4.1f} skin {e['skin']:5.1f}@{e.get('ws','')} outfit {e['outfit']:5.1f}@{e.get('wo','')} hand {e['hand']*1000:3.0f} | gapS min {gs.min():5.1f} med {np.median(gs):5.1f} max {gs.max():5.1f} gapO min {go.min():5.1f} med {np.median(go):5.1f}" + (f" | frog skin {e['fskin']:5.1f} outfit {e['foutfit']:5.1f}" if FROG else ""), flush=True); continue
        print(f"   gap {nm} {'L' if left else 'R'} head-skin min {gs.min():.1f} med {np.median(gs):.1f} max {gs.max():.1f} f0 {gs[0]:.1f} | head-outfit min {go.min():.1f} med {np.median(go):.1f} max {go.max():.1f} f0 {go[0]:.1f} | per-frame skin {np.round(gs[::4],0).tolist()}")
        fr = f" frog skin {e['fskin']:5.1f} outfit {e['foutfit']:5.1f}" if FROG else ""
        print(f"{nm:6} {cands[ci][0]:28} {'L' if left else 'R'} out {o.min():5.1f}..{o.max():5.1f} fore {fo.min():6.1f}..{fo.max():6.1f} "
              f"skin {e['skin']:5.1f} (f{e['fs']}) outfit {e['outfit']:5.1f} (f{e['fo']}) hand {e['hand']*1000:4.0f} mm{fr} | skin@ {e.get('ws','')} {e.get('sk',0):+.1f} outfit@ {e.get('wo','')}", flush=True)
