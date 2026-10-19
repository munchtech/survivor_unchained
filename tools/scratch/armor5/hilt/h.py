"""harness: python h.py [json params] -- builds run+sprint base (cached), applies hilt_carry, measures."""
import sys, json, pickle, copy, math
from pathlib import Path
W = Path(r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-5")
sys.path.insert(0, str(W / "tools" / "anim"))
import numpy as np
from keyed import Rig
from rig import DATA, Skeleton, write_clip
S = Path(__file__).parent
OUT = S / "clips"
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
import clips.run as R
import clips.sprint_stop as SS
cache = S / "base.pkl"
if cache.exists():
    base = pickle.load(open(cache, "rb"))
else:
    post = dict(R.POST); R.POST.clear(); SS.POST.clear()
    base = {"run_warden_town": R.clips(rig, ["run_warden_town"])[0],
            "sprint_warden_town": SS.sprint(rig, "run_warden_town")}
    R.POST.update(post); SS.POST.update(post)
    pickle.dump(base, open(cache, "wb"))
hilt = json.loads(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].startswith("{") else {}
frames = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
names = sys.argv[3].split(",") if len(sys.argv) > 3 else list(base)
for nm in names:
    c = R.hilt_carry(rig, copy.deepcopy(base[nm]), hilt) if hilt.get("off") is None else copy.deepcopy(base[nm])
    write_clip(c, sk, OUT)
import armscheck as A
from skin import _normals
ck = A.SocketChecker("warden")
clr = json.loads(A.CLEARANCE.read_text())["warden"]
I = ck.I
KEYS = ['chevalier_sword@hand_r', 'viking_sword@hand_r', 'oathbrand@hand_r', 'longsword@hand_r']
ARMY = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
hv = np.nonzero(ck.vbone == "hand_l")[0]
def ang(a, b):
    return math.degrees(math.acos(max(-1, min(1, float(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b))))))
for nm in names:
    Gs = ck.b.frames(ck.b.clip(nm, OUT))
    fl = frames or list(range(len(Gs)))
    worst = {}
    for f in fl:
        G = Gs[f]; P = ck.b.pose(G); ck.body.pose(P)
        N = _normals(P, ck.m.Tskin)
        Sh, E, H = (G[I[b]][:3, 3] for b in ("upperarm_l", "lowerarm_l", "hand_l"))
        Hm = G[I["hand_l"]][:3, :3]
        palm = Hm[:, 0] / np.linalg.norm(Hm[:, 0])
        el = ang(Sh - E, H - E); fa = ang(H - E, [0, -1, 0]); wb = ang(H - E, Hm[:, 1])
        pv = hv[(N[hv] @ palm) > 0.5]
        row = []
        for k in KEYS:
            d = ck.sheathed[k]; M = G[I[d["bone"]]]
            Q = (ck.pts_s[k] + d["normal"] * clr.get(d["socket"], 0)) @ M[:3, :3].T + M[:3, 3]
            keep, near, _ = ck.measure(P, ck.body, Q)
            wh = np.array([ck.where(near[j]) if keep[j] > 0 else "" for j in range(len(keep))])
            arm = np.array([any(a in w for a in ARMY) for w in wh]) & (keep > 0)
            dep = float(keep[arm].max()) if arm.any() else 0.0
            body = float(keep[(~arm) & (keep > 0)].max()) if ((~arm) & (keep > 0)).any() else 0.0
            from scipy.spatial import cKDTree
            pd = float(cKDTree(Q).query(P[pv])[0].min() * 1000)
            row.append((dep, body, pd, wh[int(np.argmax(np.where(arm, keep, -1)))] if arm.any() else ""))
        print(f"{nm[:6]} f{f:2d} el {el:5.1f} fa {fa:5.1f} wr {wb:5.1f} | " + " | ".join(f"{k[:4]} a{r[0]:5.1f} b{r[1]:4.1f} p{r[2]:5.1f} {r[3][:10]}" for k, r in zip(KEYS, row)))
