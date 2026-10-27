"""The reaver's wrap installed (armor 15 r1, 22 October 2026; heroine_outfits.py "THE WRAP").

The wrap is fitted to her final skin (heroine.glb, after every body post-step), so it needs none of the outfit
follows (nape, breast_sym, neck shape) that a fresh outfit build does. This takes a `--only reaver` build's top
meshes (reaver.top.*) into the installed reaver outfit, leaving every other piece of it as it is, and writes the top's
tuck of her skin from the wrap's own shape:

  - every point of her body (her arms left out) under the wrap, between its lower and upper edge at its own angle round
    her, is tucked as deep as keeps her skin MARGIN under its inner face, measured along her normal (10 mm a full
    tuck, as heroine_skin.gdshader draws it); her skin a hollow it bridges (her cleavage, the groove of her spine) is
    already under it and is not tucked; past its edges nothing, so her skin there stands proud of its pressed edge;
  - records as armor_tuck_write writes them (her bind point in glTF x 1e5, rounded; f32 tuck), into
    armor_tuck/reaver.top.bin.

    python tools/assets/wrap_post.py <build dir> [art dir, default godot/art/people] [--margin 0.0015] [--dry] [--tuck-only]

<build dir> holds heroine_outfit_reaver.gltf (and .bin) and wrap_reaver.strap.npz from heroine_outfits.py. The new
top data replaces the old top's and the installed .bin is written compactly (compact(): only the accessors and buffer
views still referenced, packed in order; r3). Then run cover.py --pieces
reaver.top and heroine_lod.py <art> reaver.
"""
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heroine_neck import _Gl  # noqa: E402
from breast_sym_post import _body, _vn  # noqa: E402

TUCK = 0.010   # (her shader's full tuck, metres)
REACH, SKIRT, EDGE_MARGIN = 0.015, 0.010, 0.001
# (r3: no arm-weight filter: r1's matched "upperarm" and so caught her flanks' upperarm_share skin, but it was never
# applied; her arms are left out by the facing and REACH tests below)


def skin_union(G):
    """Her body's skin AND its back graft (skin_graft: her upper back and nape, 1.386 m up), welded together by place:
    (U, F, J, W) with J/W each point's joints and weights (one of its copies). r3: _body() is the main primitive
    alone, so the wrap's back (and its tuck) saw no skin of hers above 1.386 m behind: its rows there fell to the
    front's hull and lay 9-25 mm inside her back."""
    g = G.g
    hb = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    ps = [p for p in g["meshes"][hb["mesh"]]["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    Ps, Fs, Js, Ws, o = [], [], [], [], 0
    for p in ps:
        P = G.get(p["attributes"]["POSITION"]).astype(float)
        Ps.append(P)
        Fs.append(G.get(p["indices"]).reshape(-1, 3).astype(int) + o)
        sets = ("0", "1") if "JOINTS_1" in p["attributes"] else ("0",)     # (Body 6: her body carries 8 weights)
        Js.append(np.hstack([G.get(p["attributes"]["JOINTS_" + k]).astype(int) for k in sets]))
        W = np.hstack([G.get(p["attributes"]["WEIGHTS_" + k]).astype(float) for k in sets])
        if W.max() > 1.5:
            W = W / 255.0 if W.max() <= 255 else W / 65535.0
        Ws.append(W)
        o += len(P)
    k = max(j.shape[1] for j in Js)
    Js = [np.pad(j, ((0, 0), (0, k - j.shape[1]))) for j in Js]
    Ws = [np.pad(w, ((0, 0), (0, k - w.shape[1]))) for w in Ws]
    P = np.vstack(Ps)
    _, first, wid = np.unique(np.round(P / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    wid = wid.ravel()
    F = wid[np.vstack(Fs)]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])]
    return P[first], F, np.vstack(Js)[first], np.vstack(Ws)[first], wid


def transplant(fresh, inst):
    """inst's reaver.top.* meshes replaced by fresh's (same names); the data appended to inst's .bin."""
    F, I = _Gl(fresh), _Gl(inst)
    assert F.names() == I.names(), "the builds' skeletons differ"
    mat = {m["name"]: i for i, m in enumerate(I.g["materials"])}
    buf = bytearray(I.buf)
    done = []
    for mi, m in enumerate(I.g["meshes"]):
        if not m["name"].startswith("reaver.top."):
            continue
        fm = [x for x in F.g["meshes"] if x["name"] == m["name"]]
        assert len(fm) == 1, m["name"]
        fm = json.loads(json.dumps(fm[0]))
        for p in fm["primitives"]:
            def take(ai):
                a = dict(F.g["accessors"][ai])
                assert "sparse" not in a
                x = F.get(ai)
                while len(buf) % 4:
                    buf.append(0)
                bv = {"buffer": 0, "byteOffset": len(buf), "byteLength": x.nbytes}
                t = F.g["bufferViews"][a["bufferView"]].get("target")
                if t:
                    bv["target"] = t
                buf.extend(x.tobytes())
                I.g["bufferViews"].append(bv)
                a["bufferView"] = len(I.g["bufferViews"]) - 1
                a.pop("byteOffset", None)
                I.g["accessors"].append(a)
                return len(I.g["accessors"]) - 1
            p["attributes"] = {k: take(v) for k, v in p["attributes"].items()}
            p["indices"] = take(p["indices"])
            for tg in p.get("targets", []):
                for k in list(tg):
                    tg[k] = take(tg[k])
            p["material"] = mat[F.g["materials"][p["material"]]["name"]]
        I.g["meshes"][mi] = fm
        done.append(m["name"])
    I.buf = buf
    I.g["buffers"][0]["byteLength"] = len(buf)
    print("WRAP_POST: %s replaced from the build" % ", ".join(done))
    return compact(I)


def compact(I):
    """I with only the accessors and buffer views something still references, its .bin packed in their order (no
    dead bytes left by a replaced piece)."""
    g = I.g
    used = []

    def acc(i):
        if i not in used:
            used.append(i)
    for m in g.get("meshes", []):
        for p in m["primitives"]:
            for v in p["attributes"].values():
                acc(v)
            if "indices" in p:
                acc(p["indices"])
            for tg in p.get("targets", []):
                for v in tg.values():
                    acc(v)
    for sk in g.get("skins", []):
        if "inverseBindMatrices" in sk:
            acc(sk["inverseBindMatrices"])
    for an in g.get("animations", []):
        for sm in an["samplers"]:
            acc(sm["input"])
            acc(sm["output"])
    used.sort()
    amap = {o: n for n, o in enumerate(used)}
    accs = [dict(g["accessors"][o]) for o in used]
    for a in accs:
        if "sparse" in a:
            a["sparse"] = json.loads(json.dumps(a["sparse"]))
    sp = [a["sparse"][k] for a in accs if "sparse" in a for k in ("indices", "values")]
    views = sorted({a["bufferView"] for a in accs if "bufferView" in a} | {x["bufferView"] for x in sp} |
                   {im["bufferView"] for im in g.get("images", []) if "bufferView" in im})
    vmap = {o: n for n, o in enumerate(views)}
    buf, nv = bytearray(), []
    for o in views:
        bv = dict(g["bufferViews"][o])
        while len(buf) % 4:
            buf.append(0)
        st = I.b0 + bv.get("byteOffset", 0)
        data = I.buf[st:st + bv["byteLength"]]
        bv["byteOffset"] = len(buf)
        buf.extend(data)
        nv.append(bv)
    while len(buf) % 4:
        buf.append(0)
    for a in accs:
        if "bufferView" in a:
            a["bufferView"] = vmap[a["bufferView"]]
    for x in sp:
        x["bufferView"] = vmap[x["bufferView"]]
    for im in g.get("images", []):
        if "bufferView" in im:
            im["bufferView"] = vmap[im["bufferView"]]

    def remap(p):
        p["attributes"] = {k: amap[v] for k, v in p["attributes"].items()}
        if "indices" in p:
            p["indices"] = amap[p["indices"]]
        for tg in p.get("targets", []):
            for k in list(tg):
                tg[k] = amap[tg[k]]
    for m in g.get("meshes", []):
        for p in m["primitives"]:
            remap(p)
    for sk in g.get("skins", []):
        if "inverseBindMatrices" in sk:
            sk["inverseBindMatrices"] = amap[sk["inverseBindMatrices"]]
    for an in g.get("animations", []):
        for sm in an["samplers"]:
            sm["input"], sm["output"] = amap[sm["input"]], amap[sm["output"]]
    old = len(I.buf) - I.b0
    g["accessors"], g["bufferViews"] = accs, nv
    I.buf, I.b0 = buf, 0
    g["buffers"][0]["byteLength"] = len(buf)
    print("WRAP_POST: .bin compacted %d -> %d bytes (%d accessors, %d views)" % (old, len(buf), len(accs), len(nv)))
    return I


def tuck(art, npz, margin):
    """reaver.top's tuck records (keys, values) from the wrap's shape."""
    H = _Gl(os.path.join(art, "heroine.glb"))
    U, Fw, _, _, _ = skin_union(H)
    Nw = _vn(U, Fw)
    z = np.load(npz)
    c, a, zz, R, thick = z["cxy"], z["a"], z["zz"], z["R"], float(z["thick"])
    # (her points in the build's frame: x, -z, y)
    B = np.c_[U[:, 0], -U[:, 2], U[:, 1]]
    NB = np.c_[Nw[:, 0], -Nw[:, 2], Nw[:, 1]]
    d = B[:, :2] - c
    r = np.linalg.norm(d, axis=1)
    th = np.mod(np.arctan2(d[:, 0], -d[:, 1]), 2 * np.pi)
    nu = len(a)
    f = th / (2 * np.pi / nu)
    i0 = np.floor(f).astype(int) % nu
    i1 = (i0 + 1) % nu
    w1 = f - np.floor(f)

    def at(col, zq):
        lo, hi = zz[0, col], zz[-1, col]
        ins = (zq >= lo) & (zq <= hi)
        ri = np.array([np.interp(zq[k], zz[:, col[k]], R[:, col[k]]) for k in range(len(zq))])
        return ins, ri, lo, hi
    ins0, r0, lo0, hi0 = at(i0, B[:, 2])
    ins1, r1, lo1, hi1 = at(i1, B[:, 2])
    lo, hi = lo0 * (1 - w1) + lo1 * w1, hi0 * (1 - w1) + hi1 * w1
    Rin = r0 * (1 - w1) + r1 * w1
    # (her skin facing out (not her arm's inner side against her) and within REACH outside its inner face (not her
    # arm's outer side); r1 build 2: her arm-weighted skin at her sides, left untucked, came 11-21 mm through it)
    er = np.c_[d / np.maximum(r, 1e-9)[:, None], np.zeros(len(r))]
    cosr = (NB * er).sum(1)
    dz = np.maximum(lo - B[:, 2], B[:, 2] - hi)
    near = (cosr > 0.2) & (r - Rin < REACH)
    inside = near & (dz <= 0)
    need = np.where(inside, r - Rin + margin, 0.0)
    # (past its edges, a skirt SKIRT wide: her skin eased down onto its edge's outer face, so a triangle of hers
    # spanning the edge can't stand up through it (build 2: ragged patches of skin over its lower edge, her rows
    # there 10-15 mm apart); her flesh slopes into the pressed edge)
    sk = near & (dz > 0) & (dz < SKIRT)
    e_ = np.clip(1 - dz / SKIRT, 0, 1)
    need = np.where(sk, np.maximum(r - Rin - thick + EDGE_MARGIN, 0) * e_ * e_ * (3 - 2 * e_), need)
    t = np.clip(need / TUCK, 0, 0.97)
    t[~(inside | sk)] = 0
    print("WRAP_POST: %d of her points under the wrap, %d tucked; tuck mean %.2f, max %.2f (%.1f mm)" % (
        int(inside.sum()), int((t > 0).sum()), t[t > 0].mean(), t.max(), 1000 * TUCK * t.max()))
    keys = np.round(U.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)
    k = np.nonzero(t > 0)[0]
    return keys[k], t[k]


def write_tuck(path, keys, vals):
    rec = np.zeros(len(keys), dtype=[("x", "<i4"), ("y", "<i4"), ("z", "<i4"), ("t", "<f4")])
    rec["x"], rec["y"], rec["z"], rec["t"] = keys[:, 0], keys[:, 1], keys[:, 2], vals
    with open(path, "wb") as f_:
        f_.write(struct.pack("<I", len(keys)) + rec.tobytes())
    print("WRAP_POST: %d tuck records -> %s" % (len(keys), path))


def main(a):
    def opt(n, d):
        return a[a.index(n) + 1] if n in a else d
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    build = pos[0]
    art = pos[1] if len(pos) > 1 else os.path.join(HERE, "..", "..", "godot", "art", "people")
    margin = float(opt("--margin", "0.0015"))
    keys, vals = tuck(art, os.path.join(build, "wrap_reaver.strap.npz"), margin)
    if "--dry" in a:
        return
    # (--tuck-only (body1 g4): the installed top already is the build's (a full outfit build installed whole, its .gltf
    # with sparse morph accessors the transplant can't take): only its tuck is rewritten, on the installed skin)
    if "--tuck-only" not in a:
        I = transplant(os.path.join(build, "heroine_outfit_reaver.gltf"), os.path.join(art, "heroine_outfit_reaver.gltf"))
        I.save()
    write_tuck(os.path.join(art, "armor_tuck", "reaver.top.bin"), keys, vals)
    # (r3: the index's tuck_count, as tuck_fix.py keeps it)
    ip = os.path.join(art, "armor_index.json")
    txt = open(ip, encoding="utf-8").read()
    idx = json.loads(txt)
    rows = idx if isinstance(idx, list) else idx.get("pieces", [])
    for r in rows:
        if r.get("id") == "reaver.top":
            r["tuck_count"] = int(len(keys))
    nl = "\n" if txt.endswith("\n") else ""
    open(ip, "w", encoding="utf-8", newline="\n").write(json.dumps(idx, indent=1) + nl)


if __name__ == "__main__":
    main(sys.argv[1:])
