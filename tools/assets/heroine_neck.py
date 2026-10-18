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


def match_pieces(path, field, hair=False):
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
    T = cKDTree(field["P"])
    To = cKDTree(np.concatenate([field["body"], field["head"]]) if hair else field["body"])
    hit = 0
    for si, sk in enumerate(g.get("skins", [])):
        pn = G.names(si)
        col = [field["names"].index(n) if n in field["names"] else -1 for n in pn]
        Dp = np.zeros((len(field["P"]), len(pn)))
        for k, c in enumerate(col):
            if c >= 0:
                Dp[:, k] = field["D"][:, c]
        if np.abs(field["D"]).sum() - np.abs(Dp).sum() > 1e-6 * max(1.0, np.abs(field["D"]).sum()):
            print("GRAFT_MATCH: %s lacks a joint the graft's change uses; skipped" % path)
            continue
        meshes = {n["mesh"] for n in g["nodes"] if n.get("skin") == si and "mesh" in n}
        done = set()
        for mi in meshes:
            for p in g["meshes"][mi]["primitives"]:
                at = p["attributes"]
                if "JOINTS_0" not in at or "JOINTS_1" in at or at["WEIGHTS_0"] in done:
                    continue
                done.add(at["WEIGHTS_0"])
                P = G.get(at["POSITION"]).astype(float)
                d, ix = T.query(P, k=8)
                do, _ = To.query(P)
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
