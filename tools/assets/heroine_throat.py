"""Her head's shape keys' moves of her throat made smooth, in her exported glb (heroine.glb).

Each face's key moves her jaw and chin (Saffron's 13 mm forward and down), and her throat under it went with them
until the 2 cm above SPLIT, where heroine_head.py eases every key's move out: the throat's surface bent there, so
side on Saffron's throat showed a kink under her chin and from the front a dark crescent groove; Highborn's a notch
then a bulge, like an Adam's apple; Moonlit's and Hard-won's milder (judge n1, 11 October 2026).

Here every key's move under her jaw (tools/assets/heroine_face/jaw_zone.png, the ten faces' jaw cuts at their
most) is made again as the smoothest that meets the key's own move along the zone's edge and none at SPLIT, with no
slope there either (biharmonic, over her head's points welded by place): her throat runs from her jaw down to her
neck as one even surface. Her normals under each key follow the change in her shape (the key's own normals plus
the turn of her surface's normals from the key's old move to the new), eased in over heroine_seam.py's band as
its own are.

heroine_seam.py's seam() runs this first, on every glb heroine_head.py and heroine_outfits.py write. On a glb whose
seam is already done:

    python tools/assets/heroine_throat.py godot/art/people/heroine.glb [OUT.glb]

(it does nothing on one already done: its head's extras say throat_eased).
"""
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from PIL import Image
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ZONE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "jaw_zone.png")
IN_ZONE = 0.3        # (the zone's value from which a point's move is made again)
EAR_X = 0.057        # (her ears' lobes, in the zone at its back corners: left as the keys shape them)
# (the keys that shape her face; her expressions (mouth_open, smile, ...) and ears keep their own moves)
SHAPE_KEYS = ("face_", "chin_", "jaw_")


def _vertex_normals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    n = np.zeros_like(V)
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


def throat(js, binc, chunks, hm, hp, shared, ease=None):
    """Every key's POSITION in the zone made again, its NORMAL moved with it (the change times `ease` per point, if
    given: for a glb whose key normals are eased already). Returns the keys changed and the largest change."""
    if "throat_eased" in hm.get("extras", {}):
        print("THROAT: already done - nothing done")
        return []
    P = hs._read(js, binc, hp["attributes"]["POSITION"])
    UV = hs._read(js, binc, hp["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, hp["indices"]).reshape(-1, 3)
    # (her points welded by place: the glb splits them along her UVs' seams)
    key = np.round(P / 1e-6).astype(np.int64)
    _, wi, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.ravel()
    n = len(wi)
    WT = inv[T]
    zone_img = np.asarray(Image.open(ZONE).convert("L"), np.float32) / 255
    h, w = zone_img.shape
    zv = zone_img[np.clip((UV[:, 1] * h).astype(int), 0, h - 1), np.clip((UV[:, 0] * w).astype(int), 0, w - 1)]
    z = np.zeros(n)
    np.maximum.at(z, inv, zv)
    sh = np.zeros(n, bool)
    sh[inv[shared]] = True
    # (the welded mesh's edges, and the ring of points next to SPLIT: held still too, so no slope at SPLIT)
    e = np.concatenate([WT[:, [0, 1]], WT[:, [1, 2]], WT[:, [2, 0]]])
    e = np.unique(np.sort(e, 1), axis=0)
    e = e[e[:, 0] != e[:, 1]]
    A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), (n, n)).tocsr()
    A.data[:] = 1
    ring = (A @ sh.astype(float)) > 0
    Pw = P[wi]
    free = (z >= IN_ZONE) & ~sh & ~ring & (np.abs(Pw[:, 0]) < EAR_X)
    fixed = ~free
    deg = np.asarray(A.sum(1)).ravel()
    L = sp.diags(deg) - A
    Lw = sp.diags(1 / np.maximum(deg, 1)) @ L
    Q = (Lw.T @ Lw).tocsr()
    Qff = Q[free][:, free].tocsc()
    Qfc = Q[free][:, fixed]
    solve = spl.factorized(Qff)
    targets = hp.get("targets", [])
    names = hm.get("extras", {}).get("targetNames", [])
    hn = hs._read(js, binc, hp["attributes"]["NORMAL"])
    changed = []
    worst = 0.0
    zero_held = sh | ring
    for k, t in enumerate(targets):
        if "POSITION" not in t or not (names[k] if k < len(names) else "").startswith(SHAPE_KEYS):
            continue
        D = hs._read(js, binc, t["POSITION"])
        Dw = np.zeros((n, 3))
        Dw[inv] = D
        if np.abs(Dw[free]).max() < 1e-7 and np.abs(Dw[ring]).max() < 1e-7:
            continue
        Dc = Dw.copy()
        Dc[zero_held] = 0
        Dn = Dc.copy()
        Dn[free] = np.stack([solve(-(Qfc @ Dc[fixed][:, c])) for c in range(3)], 1)
        D2 = Dn[inv]
        delta = np.linalg.norm(D2 - D, axis=1).max()
        if delta < 1e-6:
            continue
        worst = max(worst, delta)
        hs._set(js, chunks, t["POSITION"], D2, minmax=True)
        if "NORMAL" in t:
            dn = hs._read(js, binc, t["NORMAL"])
            turn = _vertex_normals(P + D2, T) - _vertex_normals(P + D, T)
            # (welded: each place's turn as its points' mean, so her UVs' seams don't show)
            tw = np.zeros((n, 3))
            np.add.at(tw, inv, turn)
            cnt = np.bincount(inv, minlength=n)[:, None]
            turn = (tw / np.maximum(cnt, 1))[inv]
            if ease is not None:
                turn = turn * ease[:, None]
            a = hn + dn + turn
            a /= np.linalg.norm(a, axis=1)[:, None] + 1e-12
            hs._set(js, chunks, t["NORMAL"], a - hn)
        changed.append(names[k] if k < len(names) else str(k))
    hm.setdefault("extras", {})["throat_eased"] = IN_ZONE
    print("THROAT: %d of her head's points made again under her jaw (%d held at SPLIT); %d keys changed, by up to "
          "%.1f mm: %s" % (int(free.sum()), int(zero_held.sum()), len(changed), worst * 1000, ", ".join(changed[:12])))
    return changed


def main(path, out=None):
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    mats = [m.get("name") for m in js.get("materials", [])]
    hm = hp = gp = None
    for m in js["meshes"]:
        for p in m["primitives"]:
            if "material" in p and mats[p["material"]] == "skin_head":
                hm, hp = m, p
            if "material" in p and mats[p["material"]] == "skin_graft":
                gp = p
    HV = hs._read(js, binc, hp["attributes"]["POSITION"])
    GV = hs._read(js, binc, gp["attributes"]["POSITION"])
    d, _ = cKDTree(GV).query(HV)
    shared = d < hs.SHARED
    ease = None
    if "seam_band" in hm.get("extras", {}):
        dist, _ = cKDTree(HV[shared]).query(HV)
        ease = hs._smooth01(dist / hm["extras"]["seam_band"])
    if throat(js, binc, chunks, hm, hp, shared, ease):
        hs._save(out or path, js, chunks)
        print("THROAT: written", out or path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
