"""P1 R1b form library: the neck, trapezius and upper back FAIRING (tools/body/designed/neck.json "neck_fair").

The R1 judge passed the neck's shape but marked MakeHuman reference-surface features showing through it in cel: two
hard cords and a groove at the back of the neck, knobs and a square corner where the trapezius meets the shoulder cap
(the acromion), a dip on the spine between the shoulder blades, the side-of-neck cords (a thin dark stripe from jaw to
collarbone). One rule fairs them, each a region of its own (the JSON's "regions", in order):

  py:neck_form.fair   per region: the region (mask "region" on V0, both sides) refilled by the biharmonic (thin-plate)
                      surface of the uniform graph Laplacian with everything outside it held (two rings: C1 at its
                      rim, breast_form.wall_delta's solve), the move toward it kept along the body's normal
                      ("normal_only", the default: no sliding of the quads) and scaled by "k" (the share of the
                      feature taken away: 0.5 = its height halved) times the C2 blend mask "blend"; then any
                      "moves" (rule "field" translate moves: {"translate": [x, y, z], "mask": [...]}). Linear in v on a
                      given body (v = 0.5: half of each); the right side is the left mirrored (exactly symmetric).

Laid before the head join (a py rule cannot be post_join): the join holds moves within 1.5 cm of the neck ring and
eases them in over 6 cm (build_topo.join_weight "ring"), so a region's top near the ring is fairly partly.
Coordinates: glTF metres, x her left (+), y up, z front (+), masks on the reference V0 (sliders.OurSliders.mask).
"""
import json
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu

import breast_form as bf

_C = {}


def _fill(sl, region, V):
    """The thin-plate refill of a region (mask > 0 on V0) with the rest held: the filled positions."""
    X = bf.extra(sl)
    key = ("fill", sl.path, json.dumps(region, sort_keys=True))
    if key not in _C:
        n = len(sl.V0)
        free = sl.mask(region, sl.V0) > 1e-9
        A = X["A"]
        deg = np.asarray(A.sum(1)).ravel()
        L = sp.identity(n, format="csr") - sp.diags(1.0 / deg) @ A
        M = (L.T @ L).tocsr()
        f, k = np.nonzero(free)[0], np.nonzero(~free)[0]
        _C[key] = (f, k, splu(M[f][:, f].tocsc()), M[f][:, k].tocsr())
    f, k, lu, Mfk = _C[key]
    W = V.copy()
    W[f] = lu.solve(-(Mfk @ V[k]))
    return W


def region_delta(sl, r, V):
    """One region's move at v = 1 on body V (left side computed, mirrored)."""
    D = np.zeros_like(V)
    if r.get("region"):
        W = _fill(sl, r["region"], V)
        d = W - V
        if r.get("normal_only", True):
            N = bf.vnormals(V, bf.extra(sl)["Q"])
            d = (d * N).sum(1, keepdims=True) * N
        w = sl.mask(r.get("blend", r["region"]), sl.V0) * float(r.get("k", 1.0))
        D += d * w[:, None]
    for m in r.get("moves", []):
        D += np.asarray(m["translate"], float)[None, :] * sl.mask(m["mask"], sl.V0)[:, None]
    return bf.mirror_left(sl, D)


def fair(sl, c, v, V, values):
    for r in c["regions"]:
        V = V + v * region_delta(sl, r, V)
    return V
