"""Her side teeth in the mouth's own shade, in her exported glb (heroine.glb): a vertex colour on her teeth.

Her teeth were lit as if the mouth were open to the sky: at the Look (her chin lifted 12 degrees) Sunborn's closed lips
leave a gap at the corner of her mouth, and the teeth behind it read as a white-pink speck (judge s1;
the solver's teeth-green test: Sunborn 44 pixels, Vixen 1). In a real mouth the teeth behind the corners stand in the
cheeks' shade (the buccal corridor), so a smile shows its front teeth lit and its side teeth darker. This gives her
teeth a grey vertex colour (COLOR_0, linear) that is how much of the front teeth's light reaches each tooth (as a share
of their brightness on screen; shaders/heroine_teeth.gdshader turns it into light). It falls with how far the tooth
stands behind the front teeth of its own row, each tooth one value: 1 on the central incisors, about 0.9 on the
laterals, 0.7 the canines, 0.55 and 0.48 the premolars, 0.4 to 0.37 the molars (each side alike, by depth, so the two
halves match whatever her sculpt's small asymmetry). Her gums and palate (one body) take it point by point. Until the
smile pass (judge j2) it fell by distance off her mouth's middle to 0.2 by 15 mm: the canines and every tooth behind
them read black in an open smile, and her far side's lower back teeth a black column through her open mouth.
(With her lips closed the whole row is darkened too, by HerFaceLife.TeethLight: from the side the corner shows her
front teeth.)

    python tools/assets/heroine_teethshade.py [GLB [OUT]] [--redo]

On one already done (its teeth mesh's extras say teeth_shade) it does nothing, unless --redo (the shade written anew).
heroine_outfits.py runs it on the body it exports, after the seam and the brow fold. Numpy only.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb")
SIDE, DEPTH, POW = 0.3, 0.007, 1.3   # (the share: SIDE + (1 - SIDE) / (1 + (d / DEPTH) ** POW), d m behind the front teeth)
MOVED = 0.002                         # (m: a point mouth_open moves more than this at 1 is her lower row's)


def _bodies(V, F):
    """Each point's body (its tooth, or the gums), points welded by position: numpy only (union-find)."""
    _, w = np.unique(np.round(V * 1e6).astype(np.int64), axis=0, return_inverse=True)
    w = w.ravel()
    par = np.arange(w.max() + 1)

    def root(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for a, b, c in w[F]:
        for p, q in ((a, b), (b, c)):
            rp, rq = root(p), root(q)
            if rp != rq:
                par[rp] = rq
    r = np.array([root(i) for i in range(len(par))])
    return r[w]


def share(V, F, moved):
    """The shade (0-1) per point: each tooth by its centroid's depth behind the front of its row, the gums by their own."""
    body = _bodies(V, F)
    ids, cnt = np.unique(body, return_counts=True)
    gum = ids[cnt.argmax()]
    cz = {b: V[body == b, 2].mean() for b in ids}
    low = {b: moved[body == b].mean() > 0.5 for b in ids}
    front = {r: max(cz[b] for b in ids if b != gum and low[b] == r) for r in (False, True)}
    d = np.array([front[low[b]] - cz[b] for b in body])
    g = body == gum
    d[g] = np.maximum(front[False] - V[g, 2], 0)
    d = np.maximum(d, 0)
    return SIDE + (1 - SIDE) / (1 + (d / DEPTH) ** POW)


def shade(path, out=None, redo=False):
    js, binc = hs._load(path)
    mats = [m.get("name") for m in js.get("materials", [])]
    hit = [(m, p) for m in js["meshes"] for p in m["primitives"] if "material" in p and mats[p["material"]] == "teeth"]
    if len(hit) != 1:
        raise SystemExit("TEETHSHADE: found %d teeth primitives" % len(hit))
    m, p = hit[0]
    if "teeth_shade" in m.get("extras", {}) and not redo:
        print("TEETHSHADE: already done in", path, "- nothing done")
        return
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    V = hs._read(js, binc, p["attributes"]["POSITION"]).astype(np.float64)
    F = hs._read(js, binc, p["indices"]).astype(np.int64).reshape(-1, 3)
    names = m.get("extras", {}).get("targetNames", [])
    moved = np.zeros(len(V), bool)
    if "mouth_open" in names:
        moved = np.linalg.norm(hs._read(js, binc, p["targets"][names.index("mouth_open")]["POSITION"]), axis=1) > MOVED
    g = share(V, F, moved)
    col = np.repeat(g[:, None], 3, 1).astype("<f4")
    bvi = len(js["bufferViews"])
    js["bufferViews"].append({"buffer": 0, "byteLength": col.nbytes})
    chunks[bvi] = col.tobytes()
    js["accessors"].append({"bufferView": bvi, "componentType": 5126, "count": len(col), "type": "VEC3"})
    p["attributes"]["COLOR_0"] = len(js["accessors"]) - 1
    m.setdefault("extras", {})["teeth_shade"] = {"side": SIDE, "depth": DEPTH, "pow": POW}
    hs._save(out or path, js, chunks)
    print("TEETHSHADE: %d points, share %.2f..%.2f (median %.2f); written %s" % (len(g), g.min(), g.max(), np.median(g), out or path))


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--redo"]
    shade(a[0] if a else GLB, a[1] if len(a) > 1 else None, redo="--redo" in sys.argv)
