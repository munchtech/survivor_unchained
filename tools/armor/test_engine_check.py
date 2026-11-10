"""The POSER held to the ENGINE's stored frames (tools/armor/engine_ref/*.npz, written by engine_check.py --store from
Godot runs of the game, 9 Nov: daggers_heavy f2, sword_heavy f10, cast_flick f6 under the warden pauldron), with no
Godot run (pytest, or python this file; about a minute: it loads her body once):
  laws    rig_drive on the engine's input pose gives the engine's output (P1Rig.cs's twin);
  patch   her tucked skin under the piece's record, posed and tucked as gear_wear does it (the look's rows merged, along
          Scene.stored_normals), lies on the engine's tucked points;
  piece   the piece's points lie on the engine's;
  sweep   gear_wear's skin test sees her shoulder through the pauldron at daggers_heavy f2 in the engine's pose (it read
          115 mm2 there before the sweep, while the game drew a torn plate).
A fail after a body, rig or gear rebuild that MEANT to change her: shoot again (engine_check.py --shoot --store)."""
import glob
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine_check as ec  # noqa: E402
import gear_wear as gw  # noqa: E402


def test_poser_is_the_engine():
    refs = sorted(glob.glob(os.path.join(ec.REF, "*.npz")))
    assert refs, "no stored engine frames"
    ix, rows = gw.load_rows(gw.GEAR)
    byid = {r["id"]: r for r in rows}
    body = os.path.join(ec.REPO, "godot", "art", "people", ix["body"])
    order = json.load(open(os.path.join(HERE, "slot_map.json"), encoding="utf-8"))["order"]
    scenes = {}
    for path in refs:
        z = np.load(path, allow_pickle=False)
        name, piece, clip = os.path.basename(path)[:-4], str(z["piece"]), str(z["clip"])
        if piece not in byid or not os.path.isfile(os.path.join(gw.CLIPS, clip + ".json")):
            print(f"{name}: skipped ({piece} or the {clip} dump is not here)")
            continue
        sc = scenes.setdefault(piece, gw.build_scene(body, rows, {piece}))
        p = sc.poser
        cp = gw.ClipPoser(sc, json.load(open(os.path.join(gw.CLIPS, clip + ".json"), encoding="utf-8")))
        Xi = np.linalg.inv(cp.X)
        to_g = lambda P: (Xi[:3, :3] @ P.T).T + Xi[:3, 3]      # noqa: E731
        nm = [str(n) for n in z["names"]]
        m4 = lambda a: np.concatenate([a, np.broadcast_to([[[0, 0, 0, 1.0]]], (len(a), 1, 4))], 1)      # noqa: E731
        pre, post, E = m4(z["pre"]), m4(z["post"]), m4(z["bones"])
        # laws
        Gout, w = p.driver.drive(p, np.stack([cp.X @ pre[nm.index(n)] for n in p.names]), sc.rig)
        mm = max(np.linalg.norm((Xi @ Gout[k])[:3, 3] - post[nm.index(n)][:3, 3]) * 1000 for k, n in enumerate(p.names))
        deg = max(ec.rot_deg((Xi @ Gout[k])[:3, :3], post[nm.index(n)][:3, :3]) for k, n in enumerate(p.names))
        ew = json.loads(str(z["weights"]))
        assert mm < ec.TOL["laws_mm"] and deg < ec.TOL["laws_deg"], (name, "laws", mm, deg)
        assert max(abs(w.get(k, 0) - ew.get(k, 0)) for k in set(w) | set(ew)) < ec.TOL["laws_w"], (name, "weights")
        # patch
        S = np.stack([cp.X @ E[nm.index(n)] for n in p.names]) @ sc.ibm
        wE = json.loads(str(z["shapes"]))
        rows_ = z["patch_row"]          # (her points by the poser's row: two of her points can share a bind key)
        assert (np.array(sc.keys)[rows_] == z["patch_key"]).all(), (name, "her body's points moved: shoot again")
        tk, gone = ec.merged_tuck(sc, byid, [str(v) for v in z["worn"]])
        u, inv = np.unique(rows_, return_inverse=True)      # (twin points of a seam share a row: Scene poses unique rows)
        idx = sc.isk[u]
        T = to_g(sc.pose(S, wE, idx) - sc.stored_normals(S, wE, idx) * tk[u][:, None])[inv]
        same = np.abs(z["patch_depth"] - tk[rows_]) < 5e-5        # (the garment tuck's under row is not gear_wear's)
        assert not gone[rows_].any() and same.mean() > 0.99, (name, "her drawn points or her tuck moved")
        # (held on the piece's own record points, as engine_check's tuck line)
        recs = gw.read_records(byid[piece]["tuck_path"])
        same &= np.array([recs.get(tuple(int(v) for v in k), 0.0) > 0 for k in z["patch_key"]])
        err = np.linalg.norm(T - z["patch_tucked"], axis=1)[same].max() * 1000
        assert err < ec.TOL["tuck_mm"], (name, "patch", err)
        # piece
        pv = np.nonzero(sc.owner == piece)[0]
        _, j = cKDTree(to_g(sc.P0[pv])).query(z["piece_rest"])
        perr = np.linalg.norm(to_g(sc.pose(S, wE, pv))[j] - z["piece_pos"], axis=1).max() * 1000
        assert perr < ec.TOL["piece_mm"], (name, "piece", perr)
        # sweep
        out2, deep = ec.out_mm2(sc, rows, order, piece, S, wE)
        print(f"{name}: laws {mm:.3f} mm {deg:.3f} deg, patch {err:.3f} mm ({int(same.sum())} points), piece {perr:.3f} mm, out {out2:.0f} mm2")
        if name == "w_dh_a":
            assert out2 > 800, (name, "the skin test went blind again", out2)


if __name__ == "__main__":
    test_poser_is_the_engine()
    print("ok")
