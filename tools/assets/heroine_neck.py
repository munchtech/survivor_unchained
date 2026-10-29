"""Her neck shortened (the owner, 18 October 2026: "our neck is just too long ... freakishly long"; slightly
long is fine, for helmets and gorgets. He picked B from the 1:1 sheet: 3 cm shorter, chin to sternal notch
about 8.5 cm, 0.37 of her head's height, the real average).

    import heroine_neck; heroine_neck.shorten_glb(<heroine.glb>, delta)     (delta in metres; 0 does nothing)

Her Head joint's rest moved `delta` down her neck's own line (its translation in neck_01's space, the neck
bone's length, shortened), her meshes and their skin left as they are. That is exactly what the game's
`--neck-cm -X` drew for the sheet (HerPose: the Head bone's pose position moved along its rest origin), now
her rest: her head, face and hair keep their shapes, the skin weighted between neck_01 and Head is drawn
shorter, and every piece and hair bound to her skeleton follows as her skin does. Run last on the glb, like
heroine_headscale.py, after every step that measures her head (the face steps find her lips by position).
"""
import json
import struct


def shorten_glb(path, delta):
    if not delta:
        return
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    rest = d[20 + jl:]
    hit = [n for n in g["nodes"] if n.get("name") == "Head"]
    assert len(hit) == 1, "one Head node"
    t = hit[0].get("translation", [0.0, 0.0, 0.0])
    L = sum(c * c for c in t) ** 0.5
    assert L > delta, "the neck is shorter than the cut"
    hit[0]["translation"] = [c * (L - delta) / L for c in t]
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = d[:12] + struct.pack("<I", len(js)) + d[16:20] + js + rest
    out = out[:8] + struct.pack("<I", len(out)) + out[12:]
    open(path, "wb").write(out)
    print("NECK_CUT %.1f mm: her Head joint's rest %.1f -> %.1f mm up her neck in %s" % (delta * 1000, L * 1000, (L - delta) * 1000, path))


# ---------------------------------------------------------------------------------------------------------------
# Her neck's skin under her head moving with her head (neck seam fix, 18 October 2026). The cut above drops every
# point 30 mm x its Head weight. Her head's skin by her ears and jaw has Head 0.5-0.76 (drops 15-23 mm) while the
# body's neck bridge under it (the skin_graft) had 0.10-0.30 (3-9 mm), so the head's skin sank onto the neck and
# the graft came out through it: 102 points by up to 8.3 mm (6, up to 1.7 mm, before the cut), the stair-stepped
# pale patch and the white shard the C01 s8/s8b/s10 close-ups showed. So each graft point within REACH of her head
# takes the weights of the head's skin it ends up beside (found again after each try, as the drop moves them),
# faded out down her neck, then smoothed over the graft's own edges: the two then drop and turn as one, at rest
# and in a turn of her head, and the neck's 3 cm is taken up lower down the graft instead of in one step at the
# head's edge. The pieces and hair that took her neck's weights in the build (the Reaver's and the Arcanist's
# collars, hair at her nape) take the same change (match_pieces), or they stay behind as the skin under them
# turns (measured: the collars let the graft through in head turns until they did).

import os

FULL, REACH = 0.02, 0.07   # graft points nearer her head than FULL (rest, m) follow it in full, fading to none at REACH
ITERS, NEAR_K, SIGMA, SMOOTH = 8, 16, 0.004, 3
PIECE_FAR = 0.03     # (a piece point farther than this from her graft took no weights from it: a hat, a hood's crown)
HAIR_NEAR, HAIR_FAR = 0.02, 0.05   # hair took her skin's weights in full within 2 cm, fading out by 5 (heroine_hair rig)

FIELD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_neck_graft.npz")
_FIELD = []    # this run's field, once match_graft has run

_CT = {5126: "<f4", 5123: "<u2", 5121: "u1", 5125: "<u4"}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


class _Gl:
    """A glb or a gltf with one .bin: read accessors, write them back in place."""

    def __init__(s, path):
        import numpy as np
        s.np, s.path = np, path
        if path.endswith(".glb"):
            d = open(path, "rb").read()
            jl = struct.unpack("<I", d[12:16])[0]
            s.g = json.loads(d[20:20 + jl])
            s.buf, s.b0, s.bin_path = bytearray(d), 20 + jl + 8, None
        else:
            s.g = json.load(open(path))
            s.bin_path = os.path.join(os.path.dirname(path), s.g["buffers"][0]["uri"])
            s.buf, s.b0 = bytearray(open(s.bin_path, "rb").read()), 0

    def _at(s, ai):
        a = s.g["accessors"][ai]
        bv = s.g["bufferViews"][a["bufferView"]]
        n = _NC[a["type"]]
        dt = s.np.dtype(_CT[a["componentType"]])
        assert bv.get("byteStride") in (None, dt.itemsize * n), "interleaved"
        return s.b0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0), dt, n, a["count"]

    def get(s, ai):
        off, dt, n, c = s._at(ai)
        return s.np.frombuffer(bytes(s.buf[off:off + dt.itemsize * n * c]), dt).reshape(c, n).copy()

    def put(s, ai, x):
        off, dt, n, c = s._at(ai)
        b = s.np.ascontiguousarray(x, dtype=dt).tobytes()
        assert len(b) == dt.itemsize * n * c
        s.buf[off:off + len(b)] = b

    def save(s):
        open(s.bin_path or s.path, "wb").write(bytes(s.buf))
        if s.bin_path:
            # (the data's checksum in the .gltf, as heroine_hair.py writes it: Godot reimports when the .gltf
            # changes, not its .bin; written back in the file's own layout)
            import hashlib
            txt = open(s.path, encoding="utf-8").read()
            s.g["asset"].setdefault("extras", {})["data"] = hashlib.md5(bytes(s.buf)).hexdigest()
            if txt.startswith("{\n\t"):
                out = json.dumps(s.g, indent="\t", separators=(",", ":"), ensure_ascii=False)
            else:
                out = json.dumps(s.g, indent=1, ensure_ascii=False)
            open(s.path, "w", encoding="utf-8", newline="\n").write(out + ("\n" if txt.endswith("\n") else ""))

    def names(s, skin=0):
        return [s.g["nodes"][j].get("name") for j in s.g["skins"][skin]["joints"]]


def _dense(J, W, nj):
    import numpy as np
    M = np.zeros((len(J), nj))
    np.add.at(M, (np.repeat(np.arange(len(J)), J.shape[1]), J.ravel().astype(int)), W.ravel())
    return M


def _top4(M):
    import numpy as np
    top = np.argsort(-M, 1)[:, :4]
    tw = np.clip(np.take_along_axis(M, top, 1), 0, None)
    tw[tw < 1e-5] = 0
    tw /= tw.sum(1, keepdims=True)
    return top, tw


def match_graft(path, delta, save=True):
    """Her graft's weights under her head made her head's (above); returns the change for match_pieces.
    delta is the cut (m) the glb has or will have; 0 does nothing."""
    if not delta:
        return None
    import numpy as np
    from scipy.spatial import cKDTree
    G = _Gl(path)
    g = G.g

    def prim(mat):
        hit = [p for m in g["meshes"] for p in m["primitives"]
               if "material" in p and g["materials"][p["material"]].get("name") == mat]
        assert len(hit) == 1, mat
        return hit[0]
    gp, hp = prim("skin_graft"), prim("skin_head")
    Pg = G.get(gp["attributes"]["POSITION"]).astype(float)
    Ph = G.get(hp["attributes"]["POSITION"]).astype(float)
    Jg, Wg = G.get(gp["attributes"]["JOINTS_0"]), G.get(gp["attributes"]["WEIGHTS_0"]).astype(float)
    Jh, Wh = G.get(hp["attributes"]["JOINTS_0"]), G.get(hp["attributes"]["WEIGHTS_0"]).astype(float)
    names = G.names()
    nj = len(names)
    hj = names.index("Head")
    # her neck's line in the world: the Head joint's offset from its parent (the cut moves it along that)
    N = g["nodes"]
    hi = [i for i, n in enumerate(N) if n.get("name") == "Head"][0]
    par = {c: i for i, n in enumerate(N) for c in n.get("children", [])}

    def world(i):
        n = N[i]
        x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * np.array(n.get("scale", [1, 1, 1]))
        return R if i not in par else world(par[i]) @ R
    up = world(par[hi]) @ np.array(N[hi]["translation"])
    up /= np.linalg.norm(up)
    Hd, Gd = _dense(Jh, Wh, nj), _dense(Jg, Wg, nj)
    Sh = Ph - delta * Hd[:, hj:hj + 1] * up
    near, nix = cKDTree(Ph).query(Pg)
    weld = near < 1e-5     # (the graft's points welded to her head's at SPLIT keep exactly the head's weights)
    t = np.clip((near - FULL) / (REACH - FULL), 0, 1)
    a = 1 - (3 * t * t - 2 * t ** 3)
    sel = a > 0
    M = Gd[sel].copy()
    Th = cKDTree(Sh)
    for _ in range(ITERS):
        r, ix = Th.query(Pg[sel] - delta * M[:, hj:hj + 1] * up, k=NEAR_K)
        q = np.exp(-((r - r[:, :1]) / SIGMA) ** 2)
        q /= q.sum(1, keepdims=True)
        M = Gd[sel] * (1 - a[sel, None]) + np.einsum("vk,vkj->vj", q, Hd[ix]) * a[sel, None]
    full = Gd.copy()
    full[sel] = M
    if SMOOTH:
        # (over the graft's edges, a point and its seam copies as one)
        F = G.get(gp["indices"]).reshape(-1, 3).astype(int)
        _, wid = np.unique(np.round(Pg, 6), axis=0, return_inverse=True)
        wid = wid.ravel()
        E = wid[np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]]
        nw = wid.max() + 1
        cnt = np.bincount(E[:, 0], minlength=nw) + np.bincount(E[:, 1], minlength=nw)
        pc = np.bincount(wid, minlength=nw).astype(float)
        for _ in range(SMOOTH):
            pw = np.zeros((nw, nj))
            np.add.at(pw, wid, full)
            pw /= pc[:, None]
            acc = np.zeros((nw, nj))
            np.add.at(acc, E[:, 0], pw[E[:, 1]])
            np.add.at(acc, E[:, 1], pw[E[:, 0]])
            sm = 0.5 * pw + 0.5 * acc / np.maximum(cnt, 1)[:, None]
            full[sel] = sm[wid[sel]]
            full[weld] = Hd[nix[weld]]
    full[weld] = Hd[nix[weld]]
    top, tw = _top4(full[sel])
    Jn, Wn = Jg.copy(), Wg.astype(np.float32).copy()
    Jn[sel], Wn[sel] = top, tw
    G.put(gp["attributes"]["JOINTS_0"], Jn)
    G.put(gp["attributes"]["WEIGHTS_0"], Wn)
    G.save()
    new = _dense(Jn, Wn.astype(float), nj)
    print("GRAFT_MATCH: %d of %d graft points take the weights of her head's skin over them (faded out %.0f mm "
          "from it) in %s" % (int(sel.sum()), len(Pg), REACH * 1000, path))
    body = [p for m in g["meshes"] for p in m["primitives"] if p is not gp and p is not hp
            and "JOINTS_0" in p["attributes"] and any(p is q for q in g["meshes"][[n for n in N if n.get("name") == "Heroine"][0]["mesh"]]["primitives"])]
    Pb = np.concatenate([G.get(p["attributes"]["POSITION"]).astype(float) for p in body])
    # (kept for builds that make pieces or hair without her body: the graft and her skin within 10 cm of the change)
    ch = np.abs(new - Gd).sum(1) > 1e-4
    Tc = cKDTree(Pg[ch])
    keep = lambda P: Tc.query(P, distance_upper_bound=0.1)[0] < 1
    kg = keep(Pg)
    fld = dict(P=Pg[kg], D=(new - Gd)[kg], names=names, body=Pb[keep(Pb)], head=Ph[keep(Ph)])
    if save:
        np.savez_compressed(FIELD_FILE, P=fld["P"].astype(np.float32), D=fld["D"].astype(np.float32),
                            names=np.array(names), body=fld["body"].astype(np.float32), head=fld["head"].astype(np.float32))
    _FIELD[:] = [fld]
    return fld


def field():
    """The graft's change for match_pieces: this run's, else the last body build's (FIELD_FILE), else None."""
    if _FIELD:
        return _FIELD[0]
    if not os.path.exists(FIELD_FILE):
        return None
    import numpy as np
    z = np.load(FIELD_FILE)
    return dict(P=z["P"].astype(float), D=z["D"].astype(float), names=[str(n) for n in z["names"]],
                body=z["body"].astype(float), head=z["head"].astype(float))


def match_pieces(path, field, hair=False, only=None):
    """A piece or hair file (glb or gltf) given the graft's change (match_graft's field) where her graft was the
    skin it took its weights from: an outfit's points took the nearest point of her body (heroine_rig's sampler,
    her head not in it), hair's the nearest of her head or body within 2 cm, fading out by 5 (heroine_hair rig).
    So each moves with the skin under it again."""
    if not field:
        return
    import numpy as np
    from scipy.spatial import cKDTree
    G = _Gl(path)
    g = G.g
    FP, FD = field["P"], field["D"]
    if not len(FP):
        return
    T = cKDTree(FP)
    Oth = np.concatenate([field["body"], field["head"]]) if hair else field["body"]
    To = cKDTree(Oth) if len(Oth) else None
    hit = 0
    for si, sk in enumerate(g.get("skins", [])):
        pn = G.names(si)
        col = [field["names"].index(n) if n in field["names"] else -1 for n in pn]
        Dp = np.zeros((len(FP), len(pn)))
        for k, c in enumerate(col):
            if c >= 0:
                Dp[:, k] = FD[:, c]
        # (a joint the piece lacks (hair has no upperarm_share) gives its change to its nearest forebear the piece has,
        # where the field knows her skeleton)
        par = field.get("parents") or {}
        for c, nm in enumerate(field["names"]):
            if nm in pn or not np.abs(FD[:, c]).any():
                continue
            up = par.get(nm)
            while up is not None and up not in pn:
                up = par.get(up)
            if up is not None:
                Dp[:, pn.index(up)] += FD[:, c]
        if np.abs(FD).sum() - np.abs(Dp).sum() > 1e-6 * max(1.0, np.abs(FD).sum()):
            print("GRAFT_MATCH: %s lacks a joint the graft's change uses; skipped" % path)
            continue
        meshes = {n["mesh"] for n in g["nodes"] if n.get("skin") == si and "mesh" in n}
        done = set()
        for mi in meshes:
            # (only: a test on the mesh's name; the cuirass grafts its leather (straps, band), never its rigid plate)
            if only is not None and not only(g["meshes"][mi].get("name", "")):
                continue
            for p in g["meshes"][mi]["primitives"]:
                at = p["attributes"]
                if "JOINTS_0" not in at or "JOINTS_1" in at or at["WEIGHTS_0"] in done:
                    continue
                done.add(at["WEIGHTS_0"])
                P = G.get(at["POSITION"]).astype(float)
                d, ix = T.query(P, k=8)
                do = To.query(P)[0] if To is not None else np.full(len(P), np.inf)
                f = ((d[:, 0] < do) & (hair | (d[:, 0] < PIECE_FAR))).astype(float)
                if hair:
                    t = np.clip((d[:, 0] - HAIR_NEAR) / (HAIR_FAR - HAIR_NEAR), 0, 1)
                    f *= 1 - (3 * t * t - 2 * t ** 3)
                q = np.exp(-((d - d[:, :1]) / SIGMA) ** 2)
                q /= q.sum(1, keepdims=True)
                Dv = np.einsum("vk,vkj->vj", q, Dp[ix]) * f[:, None]
                ok = np.abs(Dv).sum(1) > 1e-4
                if not ok.any():
                    continue
                J, W = G.get(at["JOINTS_0"]), G.get(at["WEIGHTS_0"]).astype(float)
                top, tw = _top4(_dense(J[ok], W[ok], len(pn)) + Dv[ok])
                J[ok], W[ok] = top, tw
                G.put(at["JOINTS_0"], J)
                G.put(at["WEIGHTS_0"], W.astype(np.float32))
                hit += int(ok.sum())
    if hit:
        G.save()
    print("GRAFT_MATCH: %d points of %s follow her neck's skin under them" % (hit, os.path.basename(path)))


# ---------------------------------------------------------------------------------------------------------------
# Her nape (the owner's crop at creation's Look, 20 October 2026: a step in her neck's outline just below her right
# ear, a pale wedge pointing up with her turned 40). Measured on the built glb, two faults, both her weights:
#  1. Spikes. Two points of her head's skin at her nape (x -0.038/-0.041, y 1.650, z -0.06, rest) had Head 0.05
#     (neck_01 0.65, spine_03 0.24, clavicle_r 0.06: a sample from inside her body when her head was rigged) among
#     points with Head 0.44-0.50. The cut drops each point 30 mm x its Head weight: those two dropped 1.4 mm, their
#     ring 14-20 mm, so they stood 13-18 mm up out of her nape's outline (the head's triangles round them folded
#     over, 155-174 deg). Her nape's midline row on the head-graft seam the same, softer (Head 0.16-0.18 among 0.4).
#  2. A step. Round her neck's back and sides her Head weight rose 0 -> 0.5 up the graft, held about 0.5-0.6 for
#     4 cm (match_graft gives the graft her head's rim), then 0.6 -> 1.0 within 1 cm on her head's own skin (rest
#     y 1.66-1.67): the cut took 1 cm of her skin there to 2-5 mm, a crease round her nape that her chin up folds
#     further. heroine_throat_skin.ease spread her front and sides' ramp over her whole neck, but not her back, and
#     never her head's own skin.
# The 18 Oct checks measured gaps and pokes between her head and the graft, which the two of them stepping together
# pass. So, her head, graft and body welded as one: despike refills a point whose weights stand off its ring's (L1
# > SPIKE_L1) from the points round it; ease_nape then refills every weight round her neck's back and sides, from
# where her body has no Head or neck_01 up to where her head's skin is all Head (both held), biharmonic, as ease
# did her front: the 3 cm the cut takes is spread down her nape. Weights only, so they give the same on a built glb
# (cut already) as in the build (after heroine_throat_skin.soften, before shorten_glb); once per export (nape marks
# the glb, and leaves a marked one). The points they change join the graft's field, so pieces and hair that took those weights follow
# (match_pieces: an outfit's point at her nape took the graft's weights, which are her head's skin's there). Off:
# NAPE_EASE=0.

SPIKE_L1 = 0.3                    # (a point's weights this far (L1) from its ring's mean: a spike)
NAPE_BOX = (1.50, 1.74, 0.11)     # (rest y from, to, and radius round her neck's axis, m)
NAPE_TH = 30.0                    # (deg round her neck from her front left alone: her throat, ease's; at 70 a fold
#                                    under her left ear (Head 0.55 -> 0.70 in 5 mm, rest y 1.64) stayed)
NAPE_FEATHER = 45.0               # (deg past NAPE_TH over which the eased weights blend in from her held ones. 20 Oct:
#                                    a hard edge at 45 left a crease along it under her left ear (rest y 1.64, her
#                                    throat's ramp there steeper than her right's): 7 deg -> 77 turned 45 to her right,
#                                    49 chin down. Blended 30 -> 75 it is 15 and 11, her right side the same or better)
NAPE_HEAD = 0.98                  # (her head's skin at this much Head and over is held: her face and scalp)
NAPE_LOW = 0.005                  # (Head + neck_01 under this: her back and shoulders, held)


def _nape_mesh(G):
    """Her body's, graft's and head's skin welded by place, rest: (prims, kinds, positions, offsets, weld ids, welded
    points, welded weights, edges, her neck's axis point)."""
    import numpy as np
    g = G.g
    N = g["nodes"]
    nj = len(G.names())
    hb = [n for n in N if n.get("name") == "Heroine"][0]
    hh = [n for n in N if n.get("name") == "HeroineHead"][0]
    prims = [p for p in g["meshes"][hb["mesh"]]["primitives"] if "JOINTS_0" in p["attributes"]]
    prims += [p for p in g["meshes"][hh["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") == "skin_head"]
    kind = [g["materials"][p["material"]].get("name") for p in prims]
    Ps = [G.get(p["attributes"]["POSITION"]).astype(float) for p in prims]
    D = np.concatenate([_dense(G.get(p["attributes"]["JOINTS_0"]), G.get(p["attributes"]["WEIGHTS_0"]).astype(float), nj)
                        for p in prims])
    off = np.cumsum([0] + [len(x) for x in Ps])
    P = np.concatenate(Ps)
    F = np.concatenate([G.get(p["indices"]).reshape(-1, 3).astype(int) + off[k] for k, p in enumerate(prims)])
    _, wid = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    wid = wid.ravel()
    nw = wid.max() + 1
    U = np.zeros((nw, 3))
    U[wid] = P
    Dw = np.zeros((nw, nj))
    np.add.at(Dw, wid, D)
    Dw /= np.bincount(wid, minlength=nw)[:, None]
    E = wid[np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]]
    E = np.unique(np.sort(E, 1), axis=0)
    E = E[E[:, 0] != E[:, 1]]
    par = {c: i for i, n in enumerate(N) for c in n.get("children", [])}
    i, c = [k for k, n in enumerate(N) if n.get("name") == "neck_01"][0], np.zeros(3)
    while True:
        n = N[i]
        x, y, z, w = n.get("rotation", [0, 0, 0, 1])
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * np.array(n.get("scale", [1, 1, 1]))
        c = R @ c + np.array(n.get("translation", [0, 0, 0]))
        if i not in par:
            break
        i = par[i]
    return prims, kind, Ps, off, wid, U, Dw, E, c


def _nape_write(G, prims, kind, Ps, off, wid, X, chg, names, save, merge, tag):
    """X (welded weights) written to the points chg marks; the change returned as a field for match_pieces, and
    added to this run's field (merge)."""
    import numpy as np
    from scipy.spatial import cKDTree
    nj = len(names)
    keep = []
    for k, p in enumerate(prims):
        ix = wid[off[k]:off[k + 1]]
        f = chg[ix]
        if not f.any():
            continue
        J, Wt = G.get(p["attributes"]["JOINTS_0"]), G.get(p["attributes"]["WEIGHTS_0"]).astype(np.float32)
        old = _dense(J[f], Wt[f].astype(float), nj)
        top, tw = _top4(X[ix[f]])
        J[f], Wt[f] = top, tw
        G.put(p["attributes"]["JOINTS_0"], J)
        G.put(p["attributes"]["WEIGHTS_0"], Wt)
        keep.append((Ps[k][f], _dense(top, tw, nj) - old))
    if not keep:
        return None
    if save:
        G.save()
    Pn, Dn = (np.concatenate([q[j] for q in keep]) for j in range(2))
    s = np.abs(Dn).sum(1) > 1e-6
    Pn, Dn = Pn[s], Dn[s]
    if not len(Pn):
        return None
    # (the field: the changed points, and every unchanged graft and head point within 10 cm with none, so a piece's
    # point takes the change only where the skin point it took its weights from changed; her body's others the rest)
    Tn = cKDTree(Pn)
    near = lambda Q: (Tn.query(Q, distance_upper_bound=0.1)[0] < 1) & (Tn.query(Q)[0] > 1e-6)
    pick = lambda m: np.concatenate([x for x, kk in zip(Ps, kind) if m(kk)] or [np.zeros((0, 3))])
    Pg, Ph = pick(lambda kk: kk == "skin_graft"), pick(lambda kk: kk == "skin_head")
    Pb = pick(lambda kk: kk not in ("skin_graft", "skin_head"))
    Pg, Ph, Pb = Pg[near(Pg)], Ph[near(Ph)], Pb[near(Pb)]
    fld = dict(P=np.concatenate([Pn, Pg, Ph]), D=np.concatenate([Dn, np.zeros((len(Pg) + len(Ph), nj))]),
               names=names, body=Pb, head=np.zeros((0, 3)),
               parents={G.g["nodes"][c].get("name"): G.g["nodes"][i].get("name")
                        for i, n in enumerate(G.g["nodes"]) for c in n.get("children", [])})
    if merge and _FIELD and list(_FIELD[0]["names"]) == list(names):
        f0 = _FIELD[0]
        d, j = cKDTree(f0["P"]).query(Pn)
        same = d < 1e-6
        Fd = f0["D"].copy()
        np.add.at(Fd, j[same], Dn[same])
        f0["P"] = np.concatenate([f0["P"], Pn[~same]])
        f0["D"] = np.concatenate([Fd, Dn[~same]])
        # (a head point that changed is the field's now, not one of the rest)
        if len(f0["head"]):
            f0["head"] = f0["head"][cKDTree(Pn).query(f0["head"])[0] > 1e-6]
        if save:
            np.savez_compressed(FIELD_FILE, P=f0["P"].astype(np.float32), D=f0["D"].astype(np.float32),
                                names=np.array(names), body=f0["body"].astype(np.float32), head=f0["head"].astype(np.float32))
    print("%s: %d points of her skin changed weights in %s" % (tag, int(len(Pn)), G.path))
    return fld


def _merge_fields(a, b):
    """Two changes as one field (b's after a's)."""
    if a is None or b is None:
        return a if b is None else b
    import numpy as np
    from scipy.spatial import cKDTree
    d, j = cKDTree(a["P"]).query(b["P"])
    same = d < 1e-6
    D = a["D"].copy()
    np.add.at(D, j[same], b["D"][same])
    return dict(P=np.concatenate([a["P"], b["P"][~same]]), D=np.concatenate([D, b["D"][~same]]),
                names=a["names"], parents=a.get("parents"),
                body=a["body"] if len(a["body"]) >= len(b["body"]) else b["body"], head=a["head"])


def despike(path, save=True, merge=True):
    """Her nape's weight spikes refilled from their rings (see above). Returns the change as a field, or None."""
    import numpy as np
    import scipy.sparse as sp
    G = _Gl(path)
    names = G.names()
    nj = len(names)
    prims, kind, Ps, off, wid, U, Dw, E, c = _nape_mesh(G)
    nw = len(U)
    hj = names.index("Head")
    r = np.hypot(U[:, 0] - c[0], U[:, 2] - c[2])
    th = np.degrees(np.arctan2(U[:, 0] - c[0], U[:, 2] - c[2]))
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(nw, nw)).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    ring_h = (A @ Dw[:, hj]) / np.maximum(deg, 1)
    trans = ((Dw[:, hj] > 0.02) & (Dw[:, hj] < NAPE_HEAD)) | ((ring_h > 0.02) & (ring_h < NAPE_HEAD))
    band = (U[:, 1] > NAPE_BOX[0]) & (U[:, 1] < NAPE_BOX[1]) & (r < NAPE_BOX[2]) & (np.abs(th) > NAPE_TH) & trans
    X = Dw.copy()
    bad = np.zeros(nw, bool)
    for _ in range(6):
        ok = (~bad).astype(float)
        k = A @ ok
        dev = np.abs(X - (A @ (X * ok[:, None])) / np.maximum(k, 1)[:, None]).sum(1)
        new = band & ~bad & (k > 0) & (dev > SPIKE_L1)
        if not new.any():
            break
        bad |= new
        bi = np.where(bad)[0]
        Ab = A[bi]
        for _ in range(200):     # (the spikes filled harmonically from the points round them)
            X[bi] = (Ab @ X) / np.maximum(deg[bi], 1)[:, None]
    X = np.clip(X, 0, None)
    X /= X.sum(1, keepdims=True)
    print("NAPE_SPIKES: %d of her neck's points had weights off their rings' (L1 > %.2f), refilled from them"
          % (int(bad.sum()), SPIKE_L1))
    return _nape_write(G, prims, kind, Ps, off, wid, X, bad, names, save, merge, "NAPE_SPIKES")


def ease_nape(path, save=True, merge=True):
    """Her weights round her neck's back and sides refilled (biharmonic) between her body and her head (see above).
    After despike. Returns the change as a field, or None."""
    import numpy as np
    import scipy.sparse as sp
    from scipy.sparse.linalg import splu
    G = _Gl(path)
    names = G.names()
    prims, kind, Ps, off, wid, U, Dw, E, c = _nape_mesh(G)
    nw = len(U)
    hj, nk = names.index("Head"), names.index("neck_01")
    r = np.hypot(U[:, 0] - c[0], U[:, 2] - c[2])
    th = np.degrees(np.arctan2(U[:, 0] - c[0], U[:, 2] - c[2]))
    free = (U[:, 1] > NAPE_BOX[0]) & (U[:, 1] < NAPE_BOX[1]) & (r < NAPE_BOX[2]) & (np.abs(th) > NAPE_TH) & \
        (Dw[:, hj] < NAPE_HEAD) & (Dw[:, hj] + Dw[:, nk] > NAPE_LOW)
    # (only the part of that joined to her neck's back: an ear's or a shoulder's stray point is left)
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(nw, nw)).tocsr()
    from scipy.sparse.csgraph import connected_components
    fi = np.nonzero(free)[0]
    _, lab = connected_components(A[fi][:, fi], directed=False)
    big = np.bincount(lab).argmax()
    free[fi[lab != big]] = False
    fi, bi = np.nonzero(free)[0], np.nonzero(~free)[0]
    L = (sp.diags(np.asarray(A.sum(1)).ravel()) - A).tocsr()
    L2 = (L @ L).tocsr()
    lu = splu(L2[fi][:, fi].tocsc())
    rhs = -(L2[fi][:, bi] @ Dw[bi])
    # (her head's and neck's shares solved; the rest of each point's weight kept in its own proportions (her spine,
    # clavicles, breasts), or her spine's if it had none, so no clavicle or arm is drawn up her neck)
    X = Dw.copy()
    hn_ = np.clip(np.stack([lu.solve(rhs[:, hj]), lu.solve(rhs[:, nk])], 1), 0, 1)
    hn_ /= np.maximum(hn_.sum(1, keepdims=True), 1)
    oth = Dw[fi].copy()
    oth[:, [hj, nk]] = 0
    so = oth.sum(1, keepdims=True)
    rest = 1 - hn_.sum(1, keepdims=True)
    sj = names.index("spine_03")
    none = so[:, 0] < 1e-6
    oth[~none] *= rest[~none] / so[~none]
    oth[none, sj] = rest[none, 0]
    oth[:, hj], oth[:, nk] = hn_[:, 0], hn_[:, 1]
    X[fi] = oth
    # (blended in round her neck from NAPE_TH to NAPE_TH + NAPE_FEATHER, smoothstep, so no edge between her held
    # throat and her eased nape folds in a turn)
    t = np.clip((np.abs(th) - NAPE_TH) / max(NAPE_FEATHER, 1e-6), 0, 1)
    X = Dw + (t * t * (3 - 2 * t))[:, None] * (X - Dw)
    chg = free & (np.abs(X - Dw).sum(1) > 1e-3)
    print("NAPE_EASE: %d points round her neck's back and sides refilled between her body and her head" % int(free.sum()))
    return _nape_write(G, prims, kind, Ps, off, wid, X, chg, names, save, merge, "NAPE_EASE")


NAPE_MARK = "heroine_nape"        # (the glb's asset extras, once done: ease_nape is a solve, not a fixed point)


def nape(path, save=True, merge=True):
    """despike, then ease_nape (NAPE_EASE=0: despike only), once per export (a glb marked done is left); their
    change as one field for match_pieces, or None."""
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    if g.get("asset", {}).get("extras", {}).get(NAPE_MARK):
        print("NAPE: %s has had it" % path)
        return None
    a = despike(path, save, merge)
    b = ease_nape(path, save, merge) if os.environ.get("NAPE_EASE", "1") == "1" else None
    if save:
        d = open(path, "rb").read()
        g = json.loads(d[20:20 + jl])
        g.setdefault("asset", {}).setdefault("extras", {})[NAPE_MARK] = {"spike_l1": SPIKE_L1, "th": NAPE_TH, "feather": NAPE_FEATHER,
                                                                           "ease": b is not None}
        js = json.dumps(g, separators=(",", ":")).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        out = d[:12] + struct.pack("<I", len(js)) + d[16:20] + js + d[20 + jl:]
        out = out[:8] + struct.pack("<I", len(out)) + out[12:]
        open(path, "wb").write(out)
    return _merge_fields(a, b)


# ---------------------------------------------------------------------------------------------------------------
# Her neck's seam (Face lead 32, 21 October 2026, the owner's frame from play: her LEFT neck outline jogged out
# partway down below her jaw, in town's close-up with her head turned to her right). Measured on the game's own
# frame (--hairdump in play: her skin as drawn, the camera, her bones), the jog was her skin's shape, not her
# weights: the graft's top and her head's lowest skin (rest y 1.62-1.65, round her neck's sides and back) carried
# lumps of 1-3 mm, worse on her left (her graft's left sat 2-3 mm in at rest y 1.59-1.62 where her right did not,
# her head's neck 1-1.5 mm out to her left): a 1.7 px shelf at 1080 (1.5 mm) on her left, 1.0 px on her right.
# Weights mirrored from her right changed nothing (1.74 -> 1.69 px); her right's shape mirrored onto her left took
# it to 1.06. heroine_throat_skin.soften fairs her neck's front and sides but holds the skin near the weld, and
# ease_nape is weights only, so nothing faired the seam's band. Here it is faired: Taubin (lambda/mu, so it takes
# lumps out without shrinking her neck), the welded skin of her graft and head between FAIR_Y, faded over
# FAIR_FADE at each end and round her neck from FAIR_TH off her front (her throat and the skin under her chin
# held), each point moved along its normal only (no sliding: its weights and UVs stay where they were). Positions
# and normals only, at rest (the cut moves the head's joint, not points), so the same on a built glb as in the
# build; once (FAIR_MARK). Off: NECK_FAIR=0.
FAIR_Y = (float(os.environ.get("NECK_FAIR_Y0", "1.615")), 1.68)            # (rest y, m: the band faired, whole between, faded over FAIR_FADE outside;
#                                    from 1.60 the arcanist collar's pokes rose 15 -> 23 at a 45 turn: 1.615 keeps 15)
FAIR_FADE = 0.01
FAIR_TH = (45.0, 65.0)            # (deg round her neck from her front: none within the first, whole past the second)
FAIR_ITERS = int(os.environ.get("NECK_FAIR_ITERS", "150"))   # (lambda/mu pairs: 80 -> 0.66 px left, 150 -> 0.47)
FAIR_LM = (0.5, -0.53)
FAIR_SYM = float(os.environ.get("NECK_FAIR_SYM", "1.0"))   # (share of her two sides' difference taken out first)
FAIR_MARK = "heroine_neck_fair"


def fair_seam(path, save=True):
    """Her graft's top and her head's lowest skin faired round her neck's sides and back (see above). Returns the
    largest move (m), or None when the glb has had it."""
    import numpy as np
    import scipy.sparse as sp
    G = _Gl(path)
    if G.g.get("asset", {}).get("extras", {}).get(FAIR_MARK):
        print("NECK_FAIR: %s has had it" % path)
        return None
    prims, kind, Ps, off, wid, U, Dw, E, c = _nape_mesh(G)
    nw = len(U)
    body = np.zeros(nw, bool)
    for k, kk in enumerate(kind):
        if kk not in ("skin_graft", "skin_head"):
            body[wid[off[k]:off[k + 1]]] = True
    th = np.degrees(np.arctan2(U[:, 0] - c[0], U[:, 2] - c[2]))
    r = np.hypot(U[:, 0] - c[0], U[:, 2] - c[2])

    def ss(x):
        x = np.clip(x, 0, 1)
        return x * x * (3 - 2 * x)
    f = ss((U[:, 1] - FAIR_Y[0] + FAIR_FADE) / FAIR_FADE) * ss((FAIR_Y[1] + FAIR_FADE - U[:, 1]) / FAIR_FADE) * \
        ss((np.abs(th) - FAIR_TH[0]) / (FAIR_TH[1] - FAIR_TH[0])) * (r < NAPE_BOX[2]) * ~body
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(nw, nw)).tocsr()
    Wn = (sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A).tocsr()
    F = np.concatenate([G.get(p["indices"]).reshape(-1, 3).astype(int) + off[k] for k, p in enumerate(prims)])
    Tw = wid[F]
    Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 2] != Tw[:, 0])]

    def vn(X):
        q = np.cross(X[Tw[:, 1]] - X[Tw[:, 0]], X[Tw[:, 2]] - X[Tw[:, 0]])
        n = np.zeros_like(X)
        for k in range(3):
            np.add.at(n, Tw[:, k], q)
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    N0 = vn(U)
    X = U.copy()
    if FAIR_SYM > 0:
        # (first her two sides met halfway, each point along its normal by half its distance from the other side's
        # skin mirrored (the plane through her neck's axis), so the faired band is the same each side)
        from scipy.spatial import cKDTree
        band = (U[:, 1] > FAIR_Y[0] - 2 * FAIR_FADE) & (U[:, 1] < FAIR_Y[1] + 2 * FAIR_FADE) & (r < NAPE_BOX[2])
        bi = np.nonzero(band)[0]
        M = U[bi] * [-1, 1, 1] + [2 * c[0], 0, 0]
        MN = N0[bi] * [-1, 1, 1]
        mi = np.nonzero(f > 0)[0]
        d, j = cKDTree(M).query(U[mi], k=4)
        sd = np.einsum("nkj,nkj->nk", U[mi][:, None] - M[j], MN[j]).mean(1)
        sd[d[:, 0] > 0.006] = 0
        X[mi] -= (FAIR_SYM * 0.5 * sd * f[mi])[:, None] * N0[mi]
    for _ in range(FAIR_ITERS):
        for lm in FAIR_LM:
            X = X + lm * f[:, None] * (Wn @ X - X)
    V = U + np.einsum("ij,ij->i", X - U, N0)[:, None] * N0
    mv = np.linalg.norm(V - U, axis=1)
    # (normals: each point's own turned by its surface's change, so her shading's smoothing is kept)
    dN = vn(V) - N0
    for k, p in enumerate(prims):
        if kind[k] not in ("skin_graft", "skin_head"):
            continue
        ix = wid[off[k]:off[k + 1]]
        if mv[ix].max() < 1e-6:
            continue
        G.put(p["attributes"]["POSITION"], V[ix].astype(np.float32))
        if "NORMAL" in p["attributes"]:
            Nr = G.get(p["attributes"]["NORMAL"]).astype(float) + dN[ix] * (mv[ix] > 1e-7)[:, None]
            G.put(p["attributes"]["NORMAL"], (Nr / np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-12)).astype(np.float32))
    print("NECK_FAIR: %d points of her neck's seam band faired, largest move %.2f mm, mean %.2f mm" %
          (int((mv > 1e-5).sum()), mv.max() * 1000, mv[mv > 1e-5].mean() * 1000 if (mv > 1e-5).any() else 0))
    if save:
        G.save()
        _mark(path, FAIR_MARK, {"y": FAIR_Y, "fade": FAIR_FADE, "th": FAIR_TH, "iters": FAIR_ITERS, "lm": FAIR_LM, "sym": FAIR_SYM})
    return float(mv.max())


def _mark(path, key, val):
    """The glb's asset extras given key: val (a step's done-mark)."""
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    g = json.loads(d[20:20 + jl])
    g.setdefault("asset", {}).setdefault("extras", {})[key] = val
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = d[:12] + struct.pack("<I", len(js)) + d[16:20] + js + d[20 + jl:]
    out = out[:8] + struct.pack("<I", len(out)) + out[12:]
    open(path, "wb").write(out)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "fair":
        for p_ in sys.argv[2:]:
            fair_seam(p_)
