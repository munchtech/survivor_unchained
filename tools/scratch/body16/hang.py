"""Sheathed pieces in her town clips (Body 16): their swing, depth and hand distance, rigid on the pelvis or HUNG.

usage: python hang.py [--k=0.3] [--tau=0.12] [--rigid] [--step=1] [--clips=a,b] [--keys=...]

Per clip x piece: the piece's long axis (pointing down) as angles from her body's vertical in her facing frame
(skeleton space, +Z her front, +X her left): `out` (toward her side: + away from her leg on the piece's side) and
`fore` (+ forward), min/max/amplitude over the loop; worst mm into her skin and outfit (armscheck's measure, the
clearance file as it is); the nearest hand skin to the piece (mm). The hang model is the twin of
godot/logic/Play/SheathHang.cs: the pelvis's turn in skeleton space split into its twist about her vertical (kept)
and the swing (tilt) left (kept k of it, low-passed with time constant tau), the piece turned about its pivot."""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "anim"))
import armscheck as ac  # noqa

opt = dict((a[2:].split("=", 1) + [""])[:2] for a in sys.argv[1:] if a.startswith("--"))
RIGID = "rigid" in opt
K = float(opt.get("k", 0.3))
TAU = float(opt.get("tau", 0.12))
TS = float(opt.get("ts", 0.7))
KT = float(opt["kt"]) if "kt" in opt else None
STEP = int(opt.get("step", 1))
SETS = {"warden": ["chevalier_sword@hand_r"], "reaver": ["viking_axe@hand_r", "viking_axe@hand_l"]}
CLIPS = {c: [f"idle_{c}_town", f"walk_{c}_town", f"run_{c}_town", f"sprint_{c}_town"] for c in SETS}
if "clips" in opt:
    want = opt["clips"].split(",")
    CLIPS = {c: [n for n in v if n in want] for c, v in CLIPS.items()}
PIVOT = json.loads(opt["pivot"]) if "pivot" in opt else {}   # {socket: [x,y,z] skeleton rest space}
PREST = {"pelvis": 20.6, "spine_03": -18.4}


def rotx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def quat(R):
    w = math.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = math.copysign(math.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return np.array([w, x, y, z])


def qmul(a, b):
    w1, x1, y1, z1 = a; w2, x2, y2, z2 = b
    return np.array([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2,
                     w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2])


def qinv(q):
    return q * np.array([1, -1, -1, -1])


def slerp(a, b, t):
    d = float(a @ b)
    if d < 0: b, d = -b, -d
    if d > 0.9995:
        q = a + t * (b - a); return q / np.linalg.norm(q)
    th = math.acos(d)
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


def mat(q):
    w, x, y, z = q
    return np.array([[1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
                     [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
                     [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]])


def split(q):
    """q = swing * twist, twist about +Y."""
    t = np.array([q[0], 0, q[2], 0]); n = np.linalg.norm(t)
    t = np.array([1.0, 0, 0, 0]) if n < 1e-9 else t / n
    return qmul(q, qinv(t)), t


raw = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"]
clr_all = json.loads(ac.CLEARANCE.read_text())
FING = ("index", "middle", "ring", "pinky", "thumb")
rows = []
for calling, keys in SETS.items():
    tmp = Path(__file__).with_name(f"_arms_{calling}.json")
    tmp.write_text(json.dumps({"sheathed": {k: raw[k] for k in keys}}))
    ck = ac.SocketChecker(calling, str(tmp))
    b, I, vb = ck.b, ck.I, ck.vbone
    clr = clr_all.get(calling, {})
    HAND = {s: np.array([n.endswith("_" + s) and (n.startswith("hand") or n.split("_")[0] in FING) for n in vb]) for s in "lr"}
    for name in CLIPS[calling]:
        clip = b.clip(name)
        Gs = b.frames(clip)
        dt = 1.0 / clip.fps
        for k in keys:
            d = ck.sheathed[k]
            A = np.vstack([d["mount"], [0, 0, 0, 1]])
            bone = d["bone"]
            Pr = rotx(PREST[bone])
            push = d["normal"] * clr.get(d["socket"], 0.0)
            pts_m = (np.linalg.inv(A) @ np.c_[ck.pts_s[k] + push, np.ones(len(ck.pts_s[k]))].T).T[:, :3]   # mount space
            # the long axis: mount +Y (the shaft); pointing down
            # pivot: in pelvis-local; default the mount origin
            if d["socket"] in PIVOT:
                pv = np.array(PIVOT[d["socket"]], float)
                if k.endswith("@hand_l"): pv[0] = -pv[0]
                rest = np.eye(4); rest[:3, :3] = Pr; rest[:3, 3] = (0, 1.0723, 0) if bone == "pelvis" else (0, 1.3335, 0.0364)
                pl = (np.linalg.inv(rest) @ np.r_[pv, 1])[:3]
            else:
                pl = A[:3, 3] + A[:3, :3] @ (np.array([0, 0, 0]))
            q_m = np.linalg.inv(A) @ np.r_[pl, 1]
            out_s = 1 if A[0, 3] > 0 else -1   # her left side: +X is out
            sw = None
            ang = []; deep = 0.0; odeep = 0.0; hand = 9.0; hf = -1; hs = ''
            nloop = len(Gs)
            # run the loop twice for the low-pass to settle, keep the second
            for p in range(2):
                for f in range(nloop):
                    G = Gs[f]
                    M = G[I[bone]]
                    R = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
                    if RIGID:
                        Rw = R @ A[:3, :3]
                    else:
                        D = quat(R @ Pr.T)
                        if sw is None: avg = o = D
                        avg = slerp(avg, D, 1 - math.exp(-dt / TS))
                        if KT is None:
                            tg = slerp(avg, D, K)
                        else:
                            E = qmul(qinv(avg), D); es, et = split(E)
                            I1 = np.array([1.0, 0, 0, 0])
                            tg = qmul(avg, qmul(slerp(I1, es, K), slerp(I1, et, KT)))
                        if "twistnow" in opt:
                            # the swing about the mean eased; the twist (turn about her vertical) taken now
                            E = qmul(qinv(avg), D); es, et = split(E)
                            I1 = np.array([1.0, 0, 0, 0])
                            sw2 = slerp(I1, es, K)
                            ws = sw2 if "_ws" not in dir() or f == 0 and p == 0 else slerp(_ws, sw2, 1 - math.exp(-dt / TAU))
                            _ws = ws
                            o = qmul(avg, qmul(ws, et))
                        else:
                            o = slerp(o, tg, 1 - math.exp(-dt / TAU))
                        sw = o
                        Rw = mat(o) @ Pr @ A[:3, :3]
                    pw = M[:3, :3] @ pl + M[:3, 3]
                    org = pw - Rw @ q_m[:3]
                    if p == 0 or f % STEP:
                        continue
                    y = Rw[:, 1]
                    v = y if y[1] < 0 else -y
                    ang.append((math.degrees(math.atan2(v[0] * out_s, -v[1])), math.degrees(math.atan2(v[2], -v[1]))))
                    if "fast" in opt:
                        continue
                    Q = pts_m @ Rw.T + org
                    P = b.pose(G)
                    ck.body.pose(P)
                    keep, near, _ = ck.measure(P, ck.body, Q)
                    deep = max(deep, float(keep.max()))
                    if "diag" in opt:
                        jj = int(keep.argmax()); hd, hi = cKDTree(P[HAND['l'] | HAND['r']]).query(Q)
                        print(f"   f{f:3d} skin {keep[jj]:5.1f} at y {pts_m[jj,1]:+.2f} part {vb[near[jj]]:12} | hand {hd.min()*1000:4.0f} at y {pts_m[int(hd.argmin()),1]:+.2f}")
                    dd, nr = ck.body.signed(P, Q, reach=0.14, k=8)
                    ok = np.isfinite(dd) & (dd > -0.002)
                    od = np.zeros(len(Q)); od[ok] = (ck.cover[nr[ok]] - dd[ok]) * 1000.0
                    odeep = max(odeep, float(od.max()))
                    tq = cKDTree(Q)
                    for sd in "lr":
                        h = tq.query(P[HAND[sd]])[0].min()
                        if h < hand: hand, hf, hs = h, f, sd
            a = np.array(ang)
            rows.append((name, k, a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max(), deep, odeep, hand * 1000, hf))
            print(f"{name:20} {k:22} out {a[:,0].min():6.1f}..{a[:,0].max():6.1f} ({np.ptp(a[:,0]):5.1f})  fore {a[:,1].min():6.1f}..{a[:,1].max():6.1f} ({np.ptp(a[:,1]):5.1f})  "
                  f"skin {deep:5.1f} outfit {odeep:5.1f} mm  hand {hand*1000:4.0f} mm f{hf} {hs}", flush=True)
