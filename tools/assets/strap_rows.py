"""Straps that move as one across their width (STRAP_ROWS, 21 Oct 2026, armor lead 8 round 4).

A shoulder strap is built with one set of weights across its width, eased along it (heroine_outfits.ribbon, follow
off), so in any pose each row of it moves as one piece and its edges stay two parallel lines. After export,
heroine_neck.match_pieces (her neck graft's weight change) and the nape pass add a change to each point from the skin
nearest that point: over the crest of her shoulder that gave the two edges of one row different weights (Head 0.15
on one edge, 0.26 on the other, clavicle 0.10 against 0.28), so in her idle the strap's width swung 14-20 mm from
row to row and its gold piping wavered like a hand-drawn line at the creation Look.

`even(path, frames)`: each strap's points (the strap, its gold and its stitches: whole parts lying inside the strap's
volume) take their row's mean weights again, the change kept but shared across the row. `frames` (name -> its laid
centre line, the line across it, its normal, half width, and the height band over her skin it fills, Blender axes) is
stored in the file's root extras, so a later pass (the nape) can call `even(path)` again without the build.
"""
import json
import os

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


def frame(c, bn, nrm, half, lo, hi):
    """A strap's frame for `even`: rows along `c` (n x 3, Blender axes), `bn` across, `nrm` out; its points lie within
    `half` of the line across it and `lo`..`hi` off it along `nrm`."""
    r = lambda a: np.round(np.asarray(a, float), 6).tolist()
    return {"c": r(c), "bn": r(bn), "nrm": r(nrm), "half": float(half), "lo": float(lo), "hi": float(hi)}


def even(path, frames=None, mesh_prefix=None, share=0.9, smooth=6):
    """See the module. Returns {strap: (points evened, rows)}."""
    import heroine_neck as hn
    G = hn._Gl(path)
    g = G.g
    if frames is not None:
        g.setdefault("extras", {})["strap_rows"] = frames
    frames = g.get("extras", {}).get("strap_rows") or {}
    if not frames:
        return {}
    # (every skinned primitive's points, in Blender axes, with its skin's joint names)
    prims = []
    for n in g["nodes"]:
        if "mesh" not in n or "skin" not in n:
            continue
        if mesh_prefix and not n.get("name", "").startswith(mesh_prefix):
            continue
        names = G.names(n["skin"])
        for p in g["meshes"][n["mesh"]]["primitives"]:
            at = p["attributes"]
            if "JOINTS_0" not in at or "JOINTS_1" in at:
                continue
            P = G.get(at["POSITION"]).astype(float)
            P = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)
            T = G.get(p["indices"]).reshape(-1, 3).astype(int)
            nv = len(P)
            A = sparse.coo_matrix((np.ones(len(T) * 3), (np.r_[T[:, 0], T[:, 1], T[:, 2]], np.r_[T[:, 1], T[:, 2], T[:, 0]])), shape=(nv, nv))
            cc = connected_components(A, directed=False)[1]
            prims.append(dict(at=at, P=P, cc=cc, names=names))
    allnames = sorted({nm for pr in prims for nm in pr["names"]})
    col = {nm: k for k, nm in enumerate(allnames)}
    out = {}
    for sname, f in frames.items():
        c, bn, nr = (np.asarray(f[k], float) for k in ("c", "bn", "nrm"))
        tg = np.gradient(c, axis=0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        step = np.median(np.linalg.norm(np.diff(c, axis=0), axis=1))
        tree = cKDTree(c)
        picks = []
        for pi, pr in enumerate(prims):
            P = pr["P"]
            _, j = tree.query(P)
            r = P - c[j]
            u, h, a = (r * bn[j]).sum(1), (r * nr[j]).sum(1), (r * tg[j]).sum(1)
            inside = (np.abs(u) <= f["half"]) & (h >= f["lo"]) & (h <= f["hi"]) & (np.abs(a) <= max(step, 0.002))
            fr = np.bincount(pr["cc"], inside) / np.bincount(pr["cc"])
            sel = np.nonzero(inside & (fr[pr["cc"]] >= share))[0]
            if len(sel):
                picks.append((pi, sel, j[sel]))
        if not picks:
            print("STRAP_ROWS %s: no points found in %s" % (sname, os.path.basename(path)))
            continue
        # (each picked point's weights, dense over every joint the file's skins name)
        dense = []
        for pi, sel, _ in picks:
            pr = prims[pi]
            J = G.get(pr["at"]["JOINTS_0"]).astype(int)[sel]
            W = G.get(pr["at"]["WEIGHTS_0"]).astype(float)[sel]
            M = np.zeros((len(sel), len(allnames)))
            for k in range(J.shape[1]):
                np.add.at(M, (np.arange(len(sel)), [col[pr["names"][q]] for q in J[:, k]]), W[:, k])
            dense.append(M)
        rows = np.concatenate([p[2] for p in picks])
        D = np.concatenate(dense)
        S = np.zeros((len(c), len(allnames)))
        np.add.at(S, rows, D)
        cnt = np.bincount(rows, minlength=len(c)).astype(float)
        mean = S / np.maximum(cnt, 1)[:, None]
        # (and eased along it as the build eases them (6 passes of 1-2-1): the graft's change, taken point by point, came
        # in unevenly from row to row over the crest of her shoulder, and the rows, each moving as one, stepped across)
        ok = cnt > 0
        mean[~ok] = np.array([np.interp(np.nonzero(~ok)[0], np.nonzero(ok)[0], mean[ok, q]) for q in range(mean.shape[1])]).T if (~ok).any() else mean[~ok]
        for _ in range(smooth):
            mean[1:-1] = (mean[:-2] + 2 * mean[1:-1] + mean[2:]) / 4
        spread = np.abs(D - S[rows] / np.maximum(cnt, 1)[rows, None]).sum(1)
        k0 = 0
        for (pi, sel, jr), M in zip(picks, dense):
            pr = prims[pi]
            nm = pr["names"]
            sub = mean[jr][:, [col[x] for x in nm]]
            lost = 1 - sub.sum(1) / np.maximum(mean[jr].sum(1), 1e-9)
            if lost.max() > 1e-3:
                print("STRAP_ROWS %s: up to %.3f of a row's weight is on joints this mesh's skin lacks; renormalised" % (sname, lost.max()))
            top, tw = hn._top4(sub)
            J = G.get(pr["at"]["JOINTS_0"])
            W = G.get(pr["at"]["WEIGHTS_0"]).astype(np.float32)
            J[sel] = top.astype(J.dtype)
            W[sel] = tw.astype(np.float32)
            G.put(pr["at"]["JOINTS_0"], J)
            G.put(pr["at"]["WEIGHTS_0"], W)
            k0 += len(sel)
        out[sname] = (k0, int((cnt > 0).sum()))
        print("STRAP_ROWS %s: %d points over %d rows take their row's weights (spread across a row was up to %.2f, mean %.2f)"
              % (sname, k0, int((cnt > 0).sum()), spread.max(), spread.mean()))
    G.save()
    return out
