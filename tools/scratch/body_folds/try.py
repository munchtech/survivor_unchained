import sys, os, json, numpy as np
sys.path.insert(0, os.getcwd())
import build_topo as bt
from gl import Glb
spec = bt.with_defaults(bt.load_spec("specs/her_b.json"))
A = Glb(os.path.join(bt.REPO, spec["ref"])); baked = bt.headbake.bake(A, bt.HEADS)
out = {}
for tier in ("close", "play"):
    rep = {}
    z, V = bt.stage_base(spec, tier, rep)
    V, ring, hv = bt.stage_place(spec, z, V, A, baked, rep)
    V = bt.stage_forms(spec, tier, z, V, ring, rep)
    np.save(f"{sys.argv[1]}/pre_{tier}.npy", V)
    for cfg in json.loads(sys.argv[2]):
        s2 = dict(spec, unfold=cfg); r = {}
        try:
            W = bt.stage_unfold(s2, z, V, ring, r)
        except AssertionError as e:
            print(tier, cfg, "FAIL", str(e)[:200]); continue
        u = r["unfold"]; Q = z["Q"]; T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
        hood = set(np.unique(T[u["ids_before"]]).tolist())
        hood |= {int(j) for q in Q if hood & set(q.tolist()) for j in q}
        d = np.linalg.norm(W - V, axis=1); m = np.ones(len(V), bool); m[list(hood)] = False
        print(tier, cfg, {k: u[k] for k in ("folded_before", "folded_after", "rounds", "points_moved", "move_max_mm")},
              "outside 1-ring hood max mm", round(float(d[m].max()) * 1e3, 3))
        np.save(f"{sys.argv[1]}/unf_{tier}.npy", W)
