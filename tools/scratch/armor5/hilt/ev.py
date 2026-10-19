"""in-process evaluator for hilt params."""
import sys, json, pickle, copy, math, time
from pathlib import Path
W = Path(r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-5")
sys.path.insert(0, str(W / "tools" / "anim"))
import numpy as np
from scipy.spatial import cKDTree
from keyed import Rig
from rig import DATA, Skeleton, Clip, qrot
S = Path(__file__).parent
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
import clips.run as R
base = pickle.load(open(S / "base.pkl", "rb"))
import armscheck as A
from skin import _normals
ck = A.SocketChecker("warden")
I = ck.I
XK = ["shield_round@lowerarm_l", "crossbow@hand_r"]
KEYS = ['chevalier_sword@hand_r', 'viking_sword@hand_r', 'oathbrand@hand_r', 'longsword@hand_r']
ARMY = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
hv = np.nonzero(ck.vbone == "hand_l")[0]
CLR = {"warden": 0.0155, "reaver": 0.0291, "none": 0.005}

def ang(a, b):
    return math.degrees(math.acos(max(-1, min(1, float(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b))))))

def Gframes(clip):
    # armscheck body frames from an in-memory clip: via json dict
    import tempfile, os
    d = clip.to_json(sk)
    p = S / f"tmpclips{os.getpid()}"; p.mkdir(exist_ok=True)
    (p / f"{clip.name}.json").write_text(json.dumps(d))
    return ck.b.frames(ck.b.clip(clip.name, p))

def sub(clip, fl):
    return Clip(clip.name, clip.fps, clip.rot[fl].copy(), clip.pos[fl].copy(), loop=False, meta=dict(clip.meta))

def measure(clip, fl=None, clrs=("warden", "reaver", "none"), verbose=False):
    Gs = Gframes(clip)
    fl = fl if fl is not None else range(len(Gs))
    rows = []
    for f in fl:
        G = Gs[f]; P = ck.b.pose(G); ck.body.pose(P)
        N = _normals(P, ck.m.Tskin)
        Sh, E, H = (G[I[b]][:3, 3] for b in ("upperarm_l", "lowerarm_l", "hand_l"))
        Hm = G[I["hand_l"]][:3, :3]
        palm = Hm[:, 0] / np.linalg.norm(Hm[:, 0])
        r = {"f": f, "el": ang(Sh - E, H - E), "fa": ang(H - E, [0, -1, 0]), "wr": ang(H - E, Hm[:, 1]), "H": H, "E": E}
        pv = hv[(N[hv] @ palm) > 0.5]
        for c in clrs:
            for k in KEYS + XK:
                d = ck.sheathed[k]; M = G[I[d["bone"]]]
                Q = (ck.pts_s[k] + d["normal"] * (CLR[c] if k in KEYS else json.loads(A.CLEARANCE.read_text())[c].get(d["socket"], 0))) @ M[:3, :3].T + M[:3, 3]
                keep, near, _ = ck.measure(P, ck.body, Q)
                wh = np.array([ck.where(near[j]) if keep[j] > 0 else "" for j in range(len(keep))])
                arm = np.array([any(a in w for a in ARMY) for w in wh]) & (keep > 0)
                r[(c, k, "a")] = float(keep[arm].max()) if arm.any() else 0.0
                r[(c, k, "b")] = float(keep[(~arm) & (keep > 0)].max()) if ((~arm) & (keep > 0)).any() else 0.0
                r[(c, k, "p")] = float(cKDTree(Q).query(P[pv])[0].min() * 1000)
        rows.append(r)
        if verbose:
            print(f"f{f:2d} el {r['el']:5.1f} fa {r['fa']:5.1f} wr {r['wr']:5.1f} | " + " ".join(
                f"{c[0]}:" + ",".join(f"{r[(c,k,'a')]:.1f}/{r[(c,k,'p')]:.0f}" for k in KEYS) for c in clrs))
    return rows

def apply(name, hilt, fl=None):
    c = copy.deepcopy(base[name])
    if fl is not None:
        c = sub(c, fl)
    return R.hilt_carry(rig, c, hilt)
