"""Stalker crossbow clips built in memory and measured per frame (anim 38 solver).
python ev.py [--hero] [--nox] [--all] clip ...
Per clip: each arm's worst mm into the rest of her (motion.py's zones: up/fa/hd, breast), the crossbow's worst mm
(armscheck: into her with the right arm left out, so the left hand counts) and the left hand's gap to the crossbow
(mm, palm+fingers skin to the nearest crossbow point; 0 = touching or in). --all prints every frame."""
import sys, time, importlib
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(W / "tools/anim"))
from scipy.spatial import cKDTree
from keyed import Rig
from rig import DATA, Skeleton, write_clip
from skin import Body
from motion import Measure

args = [a for a in sys.argv[1:] if not a.startswith("--")]
hero = "--hero" in sys.argv
TAG = next((a[6:] for a in sys.argv if a.startswith("--tag=")), "")
OUTD = W / "tools/anim/out" / (("anim38_hero" if hero else "anim38_her") + TAG)
OUTD.mkdir(parents=True, exist_ok=True)
sk = Skeleton.load(DATA / ("hero_skeleton.json" if hero else "heroine_skeleton.json"))
rig = Rig(sk, body="him" if hero else "her")
import pickle
import clips.idle as _idle
_b0 = _idle.base_of
def _base_of(rig_, calling):
    p = OUTD.parent / ("anim38_hero" if hero else "anim38_her") / f"base_{calling}.pkl"
    if calling not in _idle._bases and p.exists():
        _idle._bases[calling] = pickle.loads(p.read_bytes())
    out = _b0(rig_, calling)
    if not p.exists():
        p.write_bytes(pickle.dumps(out))
    return out
_idle.base_of = _base_of
FR = next((a[4:] for a in sys.argv if a.startswith("--f=")), None)
mods = [importlib.import_module(f"clips.{m}") for m in ("idle", "soul", "actions", "sprint_stop", "run")]
import os, json
for k, v in json.loads(os.environ.get("A38", "{}")).items():   # module constant overrides: {"actions.AIM_BLADE": 20}
    mn, an = k.split(".")
    setattr(importlib.import_module(f"clips.{mn}"), an, tuple(v) if isinstance(v, list) else v)
t0 = time.time()
made = []
for m in mods:
    for c in m.clips(rig, args):
        if c.name in args:
            write_clip(c, sk, OUTD); made.append(c.name)
print(f"built {made} ({time.time() - t0:.0f} s)", flush=True)

if hero:
    b = Body.hero(); ck = None; meas = Measure(b); bm = b
else:
    import armscheck as A
    ck = None if "--nox" in sys.argv else A.Checker()
    b = ck.b if ck else Body.heroine(jiggle=True, helpers=True)
    bm = Body.heroine(jiggle=True); meas = Measure(bm)   # motion.py's own (the Checker's surfaces skip the winding test)
print(f"bodies ready ({time.time() - t0:.0f} s)", flush=True)
parts = b.parts
SET = next((a[6:] for a in sys.argv if a.startswith("--set=")), "crossbow")
KEY = "crossbow@hand_r"
KEYS = [k for _, k in __import__("armscheck").SETS[SET]] if not hero else []
for n in args:
    c = b.clip(n, OUTD)
    Gs = b.frames(c)
    Gm = bm.frames(bm.clip(n, OUTD)) if bm is not b else Gs
    rows = []
    keep = range(len(Gs)) if not FR else range(*map(int, FR.split(":")))
    for f, G in enumerate(Gs):
        if f not in keep:
            rows.append({"l": (0, 0, 0, "-", False), "r": (0, 0, 0, "-", False), "x": (0, "-", 0, 999)}); continue
        P = b.pose(G)
        Pm = bm.pose(Gm[f]) if bm is not b else P
        con = meas.contact(Pm)
        r = {}
        for s in "lr":
            pts, along, _ = meas.arm[s]
            dist, _, hit, brst, near = con[s]
            ok = np.isfinite(dist)
            d = np.where(ok, -dist, -1) * 1000
            zone = np.where(along < 0.35, 0, np.where(along < 1, 1, np.where(along < 2, 2, 3)))
            z = [float(d[(zone == k) & ok].max()) if ((zone == k) & ok).any() else 0 for k in (1, 2, 3)]
            i = int(np.argmax(np.where(zone > 0, d, -9)))
            r[s] = (max(0, z[0]), max(0, z[1]), max(0, z[2]), parts[hit[i]] if hit[i] >= 0 else "-", bool(brst[i]))
        if ck:
            for s in "lr":
                ck.m.arm[s][2].pose(P)
            ck.whole.pose(P)
            xd, xw, hs = 0.0, "-", 0.0
            for K in KEYS:
                dep, nr = ck.depths(P, K, G)
                i = int(dep.argmax())
                if dep[i] > xd:
                    xd = float(dep[i]); xw = K.split("@")[0][:6] + ":" + ck.where(nr[i])
                hs = max(hs, ck.hold_depth(P, K, G)[0])
            gap = 0.0
            if SET == "crossbow":
                Q = ck.piece_points(KEY, G)
                pts, along, _ = meas.arm["l"]
                hp = P[pts[along >= 2]]   # (same skin vertices on both bodies)
                gap = float(cKDTree(Q).query(hp, k=1)[0].min()) * 1000
            r["x"] = (xd, xw, hs, gap)
        rows.append(r)
    L = np.array([max(x["l"][:3]) for x in rows]); R = np.array([max(x["r"][:3]) for x in rows])
    fl = int(L.argmax()); fr = int(R.argmax())
    s = (f"{n:22s} L {L.max():5.1f}@{fl} ({rows[fl]['l'][3]}{' br' if rows[fl]['l'][4] else ''}, up/fa/hd "
         f"{rows[fl]['l'][0]:.0f}/{rows[fl]['l'][1]:.0f}/{rows[fl]['l'][2]:.0f})  R {R.max():5.1f}@{fr} ({rows[fr]['r'][3]} {rows[fr]['r'][0]:.0f}/{rows[fr]['r'][1]:.0f}/{rows[fr]['r'][2]:.0f})")
    if ck:
        X = np.array([x["x"][0] for x in rows]); H = np.array([x["x"][2] for x in rows]); g = np.array([x["x"][3] for x in rows])
        fx = int(X.argmax())
        s += f"  X {X.max():5.1f}@{fx} ({rows[fx]['x'][1]}) hold {H.max():.1f}  gap {g.min():.1f}..{g.max():.1f}"
    print(s, f"({time.time() - t0:.0f} s)", flush=True)
    bad = [f for f in range(len(rows)) if L[f] > 0.5 or R[f] > 0.5 or (ck and rows[f]["x"][0] > 0.5)]
    show = range(len(rows)) if "--all" in sys.argv else bad
    for f in show:
        x = rows[f]
        t = f"   f{f:3d} L {L[f]:4.1f} {x['l'][3]}{'*' if x['l'][4] else ''}  R {R[f]:4.1f}"
        if ck:
            t += f"  X {x['x'][0]:4.1f} {x['x'][1]}  gap {x['x'][3]:4.1f}"
        print(t)
