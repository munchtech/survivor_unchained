"""Her head's shape keys made to keep her neck whole at SPLIT, in her exported glb (heroine.glb).

Her head is a mesh of its own, joined to the graft along SPLIT where the two share their points, and her normals there
are the two surfaces' joined (heroine_head.py's smooth_normals). But each of her head's shape keys carries normals of
its own, and Blender's glTF exporter makes them from the shaped head alone (its custom normals laid again on the
shaped head's own fans), while the graft has no keys: under any face but her own, her head's normals at the points it
shares with the graft turned from the graft's, 3 degrees on average and up to 24 (Moonlit), and the keys' own bend
of her throat above SPLIT (their moves eased out over the 2 cm above it) turned them a further 15 to 30 degrees. In
the game that drew a stepped line along SPLIT across the front of her neck, her head's side up to 30% darker
(Wildling, Vixen, Hard-won, Doe), and a dark crease under the chin (Moonlit, Saffron) (the owner, 10 October 2026).

It also gives her head's shared points the graft's skin weights (weld_weights), so the two parts move as one.

This holds every key's normals to her neck's own at SPLIT, eased into the key's over the BAND above it (as the keys'
moves are eased in, heroine_head.py's _hold), and her head's shared points unmoved by any key (they moved up to a
quarter of a millimetre), so the two parts meet as one surface under every face:

    python tools/assets/heroine_seam.py godot/art/people/heroine.glb [OUT.glb]

heroine_head.py and heroine_outfits.py run it on every heroine.glb they write. Run again on a glb written without it;
on one already done (its head's extras say seam_band and seam_weights) it does nothing.
"""
import json
import os
import struct
import sys

import numpy as np
from scipy.spatial import cKDTree

BAND = 0.02          # (metres above SPLIT over which a key's normals are eased in)
SHARED = 2e-4        # (her head's points within this of the graft's are the ones they share)
FEATHER_MM = 0.009    # (metres either side of SPLIT over which feather eases her rows into one surface)
FEATHER_ITER = 3

_CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _load(path):
    b = open(path, "rb").read()
    assert b[:4] == b"glTF", path
    off, js, binc = 12, None, b""
    while off < len(b):
        ln, ty = struct.unpack_from("<II", b, off)
        if ty == 0x4E4F534A:
            js = json.loads(b[off + 8:off + 8 + ln])
        elif ty == 0x004E4942:
            binc = b[off + 8:off + 8 + ln]
        off += 8 + ln
    return js, binc


def _view(js, binc, bvi, off, dt, count):
    bv = js["bufferViews"][bvi]
    return np.frombuffer(binc, dt, count=count, offset=bv.get("byteOffset", 0) + off)


def _read(js, binc, i):
    """An accessor's values, dense, as float64 (indices as int64)."""
    a = js["accessors"][i]
    dt, n = np.dtype(_CT[a["componentType"]]), _NC[a["type"]]
    if "bufferView" in a:
        bv = js["bufferViews"][a["bufferView"]]
        stride = bv.get("byteStride", 0) or dt.itemsize * n
        start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        raw = np.frombuffer(binc, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * n, offset=start)
        out = np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * n), (stride, 1)).copy().view(dt).reshape(a["count"], n)
    else:
        out = np.zeros((a["count"], n), dt)
    s = a.get("sparse")
    if s:
        idx = _view(js, binc, s["indices"]["bufferView"], s["indices"].get("byteOffset", 0),
                    np.dtype(_CT[s["indices"]["componentType"]]), s["count"]).astype(np.int64)
        out = out.copy()
        out[idx] = _view(js, binc, s["values"]["bufferView"], s["values"].get("byteOffset", 0), dt, s["count"] * n).reshape(-1, n)
    return out.astype(np.int64 if dt.kind in "iu" else np.float64)


def _save(path, js, chunks):
    """The glb written anew: every buffer view still used, packed in order (chunks: new views' bytes by index)."""
    used = set()
    for a in js["accessors"]:
        if "bufferView" in a:
            used.add(a["bufferView"])
        if "sparse" in a:
            used.update((a["sparse"]["indices"]["bufferView"], a["sparse"]["values"]["bufferView"]))
    for im in js.get("images", []):
        if "bufferView" in im:
            used.add(im["bufferView"])
    remap, views, body = {}, [], bytearray()
    for i in sorted(used):
        data = chunks[i]
        bv = dict(js["bufferViews"][i])
        while len(body) % 4:
            body.append(0)
        bv["byteOffset"], bv["byteLength"], bv["buffer"] = len(body), len(data), 0
        body += data
        remap[i] = len(views)
        views.append(bv)
    while len(body) % 4:
        body.append(0)
    for a in js["accessors"]:
        if "bufferView" in a:
            a["bufferView"] = remap[a["bufferView"]]
        if "sparse" in a:
            for k in ("indices", "values"):
                a["sparse"][k]["bufferView"] = remap[a["sparse"][k]["bufferView"]]
    for im in js.get("images", []):
        if "bufferView" in im:
            im["bufferView"] = remap[im["bufferView"]]
    js["bufferViews"] = views
    js["buffers"] = [{"byteLength": len(body)}]
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(body))
    out += struct.pack("<II", len(jb), 0x4E4F534A) + jb + struct.pack("<II", len(body), 0x004E4942) + bytes(body)
    open(path, "wb").write(out)


def _set(js, chunks, i, vals, minmax=False):
    """Accessor i given these values: sparse (only the rows not zero), or whole where that is smaller."""
    a = js["accessors"][i]
    vals = vals.astype(np.float32)
    rows = np.where(np.abs(vals).max(1) > 0)[0].astype(np.uint32)
    for k in ("bufferView", "byteOffset", "sparse"):
        a.pop(k, None)
    if len(rows) * (4 + vals.shape[1] * 4) > vals.nbytes:
        a["bufferView"] = len(js["bufferViews"])
        js["bufferViews"].append({"buffer": 0})
        chunks[a["bufferView"]] = vals.tobytes()
    elif len(rows):
        iv, vv = len(js["bufferViews"]), len(js["bufferViews"]) + 1
        js["bufferViews"] += [{"buffer": 0}, {"buffer": 0}]
        chunks[iv], chunks[vv] = rows.tobytes(), vals[rows].tobytes()
        a["sparse"] = {"count": int(len(rows)), "indices": {"bufferView": iv, "componentType": 5125},
                       "values": {"bufferView": vv}}
    if minmax:
        a["min"], a["max"] = [float(v) for v in vals.min(0)], [float(v) for v in vals.max(0)]


def _set_dense(js, chunks, i, vals):
    """Accessor i given these values whole, in its own component type (joints are integers)."""
    a = js["accessors"][i]
    vals = np.ascontiguousarray(vals.astype(_CT[a["componentType"]]))
    for k in ("bufferView", "byteOffset", "sparse"):
        a.pop(k, None)
    a["bufferView"] = len(js["bufferViews"])
    js["bufferViews"].append({"buffer": 0})
    chunks[a["bufferView"]] = vals.tobytes()


def weld_weights(js, binc, chunks, hp, gp, HV, GV):
    """Her head's points it shares with the graft given the graft's skin weights there, so the two move as one.
    Two at the back left of her nape carried Head 0.027 on the head and 0.40 on the graft: any turn of her head
    (a nod, the neck slider) opened a crack between them, about 0.5 cm on a 20-degree nod. Returns how many
    points changed."""
    d, gi = cKDTree(GV).query(HV)
    shared = np.where(d < SHARED)[0]
    changed = np.zeros(len(HV), bool)
    sets = sorted(k[len("JOINTS_"):] for k in hp["attributes"] if k.startswith("JOINTS_"))
    assert sets == sorted(k[len("JOINTS_"):] for k in gp["attributes"] if k.startswith("JOINTS_")), "head and graft weight sets differ"
    loaded = {}
    for n in sets:
        for kind in ("JOINTS_", "WEIGHTS_"):
            h = _read(js, binc, hp["attributes"][kind + n])
            g = _read(js, binc, gp["attributes"][kind + n])
            changed[shared] |= np.abs(h[shared] - g[gi[shared]]).max(1) > 1e-6
            h[shared] = g[gi[shared]]
            loaded[kind + n] = h
    if changed.any():
        for k, v in loaded.items():
            _set_dense(js, chunks, hp["attributes"][k], v)
    return int(changed.sum())


def _smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _lip_step(path, out=None):
    """Her upper lip's sculpt brought down to each face's portrait (heroine_lipsculpt.py), after the throat and the
    seam; once only (marker lip_sculpt). WIP, off unless HEROINE_LIPSCULPT=1."""
    import heroine_lipsculpt
    heroine_lipsculpt.run(path, out)


def feather(path, out=None):
    """Her neck's seam feathered: the points her head shares with the graft given the normal of the rows either side
    of them (the mean of her head's next row's normals and the graft's, each its own mean), once (marker
    seam_feather). The shared points' normals were the two surfaces' joined at the seam itself, where the two meet
    at a slight crease: on the front of her throat they pitched down from both rows by up to 10.6 deg (p90 8.5), and
    the game drew a 2-3 px dark ring round her neck at the Look and the close-up, 5-10 levels deeper than the skin
    either side (P1 R1 round 36; A and B alike, B's ring is A's). Her keys' normals are held to these at SPLIT (seam)."""
    js, binc = _load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    mats = [m.get("name") for m in js.get("materials", [])]
    hp = gp = hm = None
    for m in js["meshes"]:
        for p in m["primitives"]:
            if "material" in p and mats[p["material"]] == "skin_head":
                hm, hp = m, p
            if "material" in p and mats[p["material"]] == "skin_graft":
                gp = p
    if hp is None or gp is None:
        print("FEATHER: no head and graft in", path, "- nothing done")
        return
    if "seam_feather" in hm.get("extras", {}):
        print("FEATHER: already done in", path, "- nothing done")
        return
    HV = _read(js, binc, hp["attributes"]["POSITION"]).astype(np.float64)
    GV = _read(js, binc, gp["attributes"]["POSITION"]).astype(np.float64)
    HN = _read(js, binc, hp["attributes"]["NORMAL"]).astype(np.float64)
    GN = _read(js, binc, gp["attributes"]["NORMAL"]).astype(np.float64)

    def welded_adj(V, prim):
        T = _read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
        _, w = np.unique(np.round(V * 1e5).astype(np.int64), axis=0, return_inverse=True)
        w = w.ravel()
        E = w[np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])]
        adj = {}
        for a, b in E:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        return w, adj

    def unit(x):
        return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)

    hw, hadj = welded_adj(HV, hp)
    gw, gadj = welded_adj(GV, gp)
    d, gi = cKDTree(GV).query(HV)
    shared = np.where(d < SHARED)[0]
    hring, gring = set(hw[shared]), set(gw[gi[shared]])
    # (each welded point's normal: its first copy's; copies share it)
    hrep = np.zeros(hw.max() + 1, np.int64)
    hrep[hw[::-1]] = np.arange(len(hw))[::-1]
    grep_ = np.zeros(gw.max() + 1, np.int64)
    grep_[gw[::-1]] = np.arange(len(gw))[::-1]
    done, turn = 0, []
    for i in shared:
        hn = [hrep[j] for j in hadj.get(hw[i], ()) if j not in hring]
        gn = [grep_[j] for j in gadj.get(gw[gi[i]], ()) if j not in gring]
        if not hn or not gn:
            continue
        n = unit(unit(unit(HN[hn]).mean(0)) + unit(unit(GN[gn]).mean(0)))
        turn.append(np.degrees(np.arccos(np.clip(unit(HN[i]) @ n, -1, 1))))
        HN[hw == hw[i]] = n
        GN[gw == gw[gi[i]]] = n
        done += 1
    # (then the rows either side eased toward their neighbours' over FEATHER_MM, the ring held: the ring alone left
    # a fainter line at the Look, p50 3.8 -> 1.7 levels, p90 8.1 -> 5.9; round 36)
    rp = HV[shared]
    for V, N, w, adj, ring_ in ((HV, HN, hw, hadj, hring), (GV, GN, gw, gadj, gring)):
        nn = w.max() + 1
        rep = np.zeros(nn, np.int64)
        rep[w[::-1]] = np.arange(len(w))[::-1]
        dist = cKDTree(rp).query(V[rep])[0]
        a = 0.5 * (1.0 - _smooth01(dist / FEATHER_MM))
        Nw = unit(N[rep].copy())
        band = [k for k in range(nn) if a[k] > 1e-3 and k not in ring_]
        for _ in range(FEATHER_ITER):
            new = Nw.copy()
            for k in band:
                nb = list(adj.get(k, ()))
                if nb:
                    new[k] = unit((1.0 - a[k]) * Nw[k] + a[k] * unit(Nw[nb].mean(0)))
            Nw = new
        N[:] = Nw[w]
    _set_dense(js, chunks, hp["attributes"]["NORMAL"], HN.astype(np.float32))
    _set_dense(js, chunks, gp["attributes"]["NORMAL"], GN.astype(np.float32))
    hm.setdefault("extras", {})["seam_feather"] = 2
    _save(out or path, js, chunks)
    t = np.array(turn) if turn else np.zeros(1)
    print("FEATHER: %d of %d shared points given their rows' normal (turned p50 %.1f, p90 %.1f, max %.1f deg); written %s"
          % (done, len(shared), np.median(t), np.percentile(t, 90), t.max(), out or path))


def seam(path, out=None, band=BAND):
    _seam(path, out, band)
    feather(out if out and os.path.exists(out) else path, out)


def _seam(path, out=None, band=BAND):
    js, binc = _load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    mats = [m.get("name") for m in js.get("materials", [])]

    def prim_of(mat):
        for m in js["meshes"]:
            for p in m["primitives"]:
                if "material" in p and mats[p["material"]] == mat:
                    return m, p
        return None, None
    hm, hp = prim_of("skin_head")
    _, gp = prim_of("skin_graft")
    if hp is None or gp is None or not hp.get("targets"):
        print("SEAM: no head with keys and graft in", path, "- nothing done")
        return
    HV = _read(js, binc, hp["attributes"]["POSITION"])
    GV = _read(js, binc, gp["attributes"]["POSITION"])
    d, _ = cKDTree(GV).query(HV)
    shared = d < SHARED
    assert shared.sum() > 20, "her head shares only %d points with the graft" % shared.sum()
    # (how far each of her head's points is from SPLIT: from the nearest point it shares with the graft)
    dist, _ = cKDTree(HV[shared]).query(HV)
    w = _smooth01(dist / band)[:, None]
    names = hm.get("extras", {}).get("targetNames", [])
    # (both parts must be skinned by one skin for their joint indices to agree)
    skin_of = {n["mesh"]: n.get("skin") for n in js["nodes"] if "mesh" in n}
    gm = next(m for m in js["meshes"] if gp in m["primitives"])
    assert skin_of[js["meshes"].index(hm)] == skin_of[js["meshes"].index(gm)], "her head and the graft have different skins"
    welded = None
    if "seam_weights" not in hm.get("extras", {}):
        welded = weld_weights(js, binc, chunks, hp, gp, HV, GV)
        hm.setdefault("extras", {})["seam_weights"] = 1
        print("SEAM: %d of her head's points shared with the graft given the graft's skin weights" % welded)
    if "seam_band" in hm.get("extras", {}):
        if welded is not None:
            _save(out or path, js, chunks)
            print("SEAM: keys already held in", path, "- weights welded, written", out or path)
            _lip_step(out or path)
        else:
            print("SEAM: already done in", path, "(band %.0f mm) - nothing done" % (hm["extras"]["seam_band"] * 1000))
            _lip_step(path, out)
        return
    # (first her keys' moves under her jaw made smooth down to SPLIT: heroine_throat.py; then read anew, its
    # accessors being in new views)
    import heroine_throat
    if heroine_throat.throat(js, binc, chunks, hm, hp, shared):
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), "heroine_seam_%d.glb" % os.getpid())
        _save(tmp, js, chunks)
        js, binc = _load(tmp)
        os.remove(tmp)
        chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
        mats = [m.get("name") for m in js.get("materials", [])]
        hm, hp = prim_of("skin_head")
    turned, moved = [], 0.0
    hn = _read(js, binc, hp["attributes"]["NORMAL"])
    for k, t in enumerate(hp["targets"]):
        if "NORMAL" in t:
            dn = _read(js, binc, t["NORMAL"])
            dn2 = dn * w
            if np.abs(dn2 - dn).max() > 1e-6:
                a = hn + dn
                a /= np.linalg.norm(a, axis=1)[:, None] + 1e-12
                ang = np.degrees(np.arccos(np.clip((a[shared] * hn[shared]).sum(1), -1, 1)))
                turned.append((ang.max(), names[k] if k < len(names) else str(k)))
                _set(js, chunks, t["NORMAL"], dn2)
        if "POSITION" in t:
            dp = _read(js, binc, t["POSITION"])
            if np.abs(dp[shared]).max() > 0:
                moved = max(moved, np.linalg.norm(dp[shared], axis=1).max())
                dp[shared] = 0
                _set(js, chunks, t["POSITION"], dp, minmax=True)
    hm.setdefault("extras", {})["seam_band"] = band
    _save(out or path, js, chunks)
    _lip_step(out or path)
    turned.sort(reverse=True)
    print("SEAM: %d of her head's points shared with the graft; %d keys' normals held to her neck's at SPLIT (they had "
          "turned up to %.1f deg there: %s), eased in over %.0f mm; shared points' moves under the keys (up to %.2f mm) "
          "taken off; written %s" % (shared.sum(), len(turned), turned[0][0] if turned else 0,
                                     ", ".join("%s %.1f" % (n, a) for a, n in turned[:4]), band * 1000, moved * 1000,
                                     out or path))


if __name__ == "__main__":
    seam(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
