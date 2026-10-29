"""Search the HipBlade row (Body 16): her left arm (forearm, hand, fingers) against the hung sword over the warden's
town walk, run and sprint, and her trunk/legs against it; the idle's hand kept on the hilt is reported.
usage: python search.py [--rows=FILE] (each line: x,y,z;back,out  -- At, the blade's back and out lean in degrees)"""
import json, math, sys, pickle
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.argv = [sys.argv[0], "--fast", "--clips=none"] + sys.argv[1:]
sys.path.insert(0, str(Path(__file__).parent))
import hang as h

ac = h.ac
STEP = int(h.opt.get('sstep', 2))
opt = h.opt
ck = ac.SocketChecker("warden", None)
b, I, vb = ck.b, ck.I, ck.vbone
d = ck.sheathed["chevalier_sword@hand_r"]
A0 = np.vstack([d["mount"], [0, 0, 0, 1]])
CL = json.loads(ac.CLEARANCE.read_text())["warden"]["hip_blade"]
u = (np.linalg.inv(A0) @ np.c_[ck.pts_s["chevalier_sword@hand_r"], np.ones(len(ck.pts_s["chevalier_sword@hand_r"]))].T).T[:, :3]
FING = ("index", "middle", "ring", "pinky", "thumb")
ARM = np.array([n.endswith("_l") and (n.startswith("hand") or n.startswith("lowerarm") or n.split("_")[0] in FING) for n in vb])
HAND = np.array([n.endswith("_l") and (n.startswith("hand") or n.split("_")[0] in FING) for n in vb])
REST = np.eye(4); REST[:3, :3] = h.rotx(20.6); REST[:3, 3] = (0, 1.0723, 0)
cache = Path(__file__).with_name("_poses.pkl")
CL_NAMES = ["idle_warden_town", "walk_warden_town", "run_warden_town", "sprint_warden_town"]
if cache.exists():
    poses = pickle.loads(cache.read_bytes())
else:
    poses = {}
    for n in CL_NAMES:
        clip = b.clip(n); Gs = b.frames(clip)
        poses[n] = (1 / clip.fps, [G[I["pelvis"]] for G in Gs], [b.pose(G) for G in Gs])
    cache.write_bytes(pickle.dumps(poses))


def row_mount(at, back, out):
    bk, ot = math.radians(back), math.radians(out)
    shaft = np.array([math.sin(ot), -math.cos(bk) * math.cos(ot), -math.sin(bk) * math.cos(ot)])
    shaft /= np.linalg.norm(shaft)
    thick = np.array([1.0, 0, 0]); thick -= shaft * thick.dot(shaft); thick /= np.linalg.norm(thick)
    S = np.eye(4); S[:3, :3] = np.column_stack([np.cross(shaft, thick), shaft, thick]); S[:3, 3] = np.array(at) + np.array([CL, 0, 0])
    return np.linalg.inv(REST) @ S


def run(at, back, out, k=0.2, tau=0.2, ts=1.5):
    A = row_mount(at, back, out)
    pl = A[:3, 3]; qm = np.linalg.inv(A) @ np.r_[pl, 1]
    res = {}
    for n in CL_NAMES:
        dt, Ms, Ps = poses[n]
        arm, hand, body, avg, o = 9, 9, 9, None, None
        for p in range(2):
            for f, (M, P) in enumerate(zip(Ms, Ps)):
                if f % STEP: continue
                R = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
                D = h.quat(R @ h.rotx(20.6).T)
                if avg is None: avg = o = D
                avg = h.slerp(avg, D, 1 - math.exp(-dt / ts)); o = h.slerp(o, h.slerp(avg, D, k), 1 - math.exp(-dt / tau))
                if p == 0: continue
                Rw = h.mat(o) @ h.rotx(20.6) @ A[:3, :3]
                org = M[:3, :3] @ pl + M[:3, 3] - Rw @ qm[:3]
                Q = u @ Rw.T + org
                t = cKDTree(Q)
                hand = min(hand, t.query(P[HAND])[0].min())
                ck.body.pose(P)
                keep, near, _ = ck.measure(P, ck.body, Q)
                isarm = ARM[near] | np.array([vb[j].startswith("upperarm") for j in near])
                da = float(keep[isarm].max()) if isarm.any() else 0.0
                db = float(keep[~isarm].max()) if (~isarm).any() else 0.0
                arm = da if arm == 9 else max(arm, da); body = db if body == 9 else max(body, db)
        res[n] = (arm, hand * 1000, body)
    return res


rows = [l.strip() for l in Path(opt["rows"]).read_text().splitlines() if l.strip()] if "rows" in opt else ["0.21,1.20,0.10;30,0"]
for r in rows:
    a, ang = r.split(";")
    at = [float(x) for x in a.split(",")]; back, out = (float(x) for x in ang.split(","))
    res = run(at, back, out)
    print(f"{r:28} " + "  ".join(f"{n.split('_')[0]} arm {v[0]:4.0f} body {v[2]:4.0f} hand {v[1]:3.0f}" for n, v in res.items()), flush=True)
