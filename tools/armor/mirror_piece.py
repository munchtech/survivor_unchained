"""Mirror one side of a two-sided piece onto the other (Body 15, 26 October 2026: the warden's left pauldron read pale
glassy silver by day while the right read navy as designed; its two plates were not mirror twins, 62% of the left's
points within 2 mm of a mirrored right point, the matched normals' dot 0.21).

Each named mesh (one primitive, both sides in it as separate islands, split by the sign of x; each side's vertices one
run and its triangles one run, as the outfit export lays them) gets its DST side rebuilt as an exact mirror of its SRC
side; the SRC side's data is kept as it is, in its own order:
  - POSITION and NORMAL: x -> -x; triangles: the source's, winding flipped;
  - TEXCOORD_*, COLOR_0 and WEIGHTS_*: copied (the mirror shares the source's paint);
  - JOINTS_*: each joint swapped for its opposite-side twin by name (_l <-> _r; unpaired joints keep their own);
  - morph targets (sparse or dense): the source's X_r delta becomes the mirror's X_l delta (mirrored), X_l -> X_r,
    unsided names mirror onto themselves; both POSITION and NORMAL;
  - the mesh's extras "pieces" (heroine_lod.py's slot join: [place, triangles] a piece, each piece one vertex run):
    the mirror's runs are the source's runs, under the destination's own place numbers in order (the two sides must
    have as many pieces; --pieces-free: past the destination's last place, that place repeats).
New accessors are appended (gltf_compact.py drops the old buffer views afterwards). Nothing else in the file changes.

    python tools/armor/mirror_piece.py FILE.gltf --meshes warden.pauldrons.steel,warden.pauldrons.gold [--from right] [--dry]

    python tools/armor/mirror_piece.py --records REC.bin[,REC2.bin] --body godot/art/people/heroine.glb [--from right] [--dry]

--from right (default): the right side (x < 0, her right) is the source, the left (x > 0) rebuilt. Prints MIRROR lines.
--records: a piece's armor_tuck / armor_cover records mirrored the same way onto her body's points (mirror_records).
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
from heroine_neck import _Gl  # noqa: E402
from shoulder_psd_post import _read_sparse  # noqa: E402
from body_follow_post import _append, _sparse_g  # noqa: E402

_CT = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "u1"}


def _twin(name):
    if re.search(r"_l$", name):
        return name[:-2] + "_r"
    if re.search(r"_r$", name):
        return name[:-2] + "_l"
    return name


def _acc(G, arr, like, minmax=False):
    """A new accessor of `arr` in the component type and type of accessor `like`."""
    a0 = G.g["accessors"][like]
    dt = _CT[a0["componentType"]]
    arr = np.ascontiguousarray(arr, dtype=dt)
    bv = _append(G, arr.tobytes())
    a = {"bufferView": bv, "componentType": a0["componentType"], "count": int(len(arr)), "type": a0["type"]}
    if a0.get("normalized"):
        a["normalized"] = True
    if minmax:
        a["min"] = [float(x) for x in arr.reshape(len(arr), -1).min(0)]
        a["max"] = [float(x) for x in arr.reshape(len(arr), -1).max(0)]
    G.g["accessors"].append(a)
    return len(G.g["accessors"]) - 1


def mirror_mesh(G, mi, src_right=True, pieces_free=False):
    g = G.g
    m = g["meshes"][mi]
    assert len(m["primitives"]) == 1, f"{m['name']}: {len(m['primitives'])} primitives"
    p = m["primitives"][0]
    at = p["attributes"]
    X = G.get(at["POSITION"]).astype(np.float64)
    I = G.get(p["indices"]).reshape(-1, 3).astype(np.int64)
    n = len(X)
    S = (X[:, 0] < 0) if src_right else (X[:, 0] > 0)
    D = ~S
    tS, tD = S[I].all(1), D[I].all(1)
    assert (tS | tD).all(), f"{m['name']}: triangles span both sides"
    sv, dv = np.where(S)[0], np.where(D)[0]
    st, dt_ = np.where(tS)[0], np.where(tD)[0]
    # each side one vertex run and one triangle run
    for nm, v, t in (("src", sv, st), ("dst", dv, dt_)):
        assert v[-1] - v[0] + 1 == len(v) and t[-1] - t[0] + 1 == len(t), f"{m['name']}: {nm} side not one run"
    dst_first = dv[0] < sv[0]
    assert (dt_[0] < st[0]) == dst_first, f"{m['name']}: triangles and vertices in different side orders"
    ns = len(sv)
    # new layout: mirror block where the destination was, the source block as it is
    if dst_first:
        new_of_src, new_of_mir = np.arange(ns) + ns, np.arange(ns)
    else:
        new_of_src, new_of_mir = np.arange(ns), np.arange(ns) + ns
    # positions of the new vertex array: index k -> (old source index, mirrored?)
    src_idx = np.empty(2 * ns, np.int64)
    mir = np.zeros(2 * ns, bool)
    src_idx[new_of_src] = sv
    src_idx[new_of_mir] = sv
    mir[new_of_mir] = True
    flip3 = np.array([-1.0, 1.0, 1.0])

    names = G.names(g["nodes"][[i for i, nd in enumerate(g["nodes"]) if nd.get("mesh") == mi][0]].get("skin", 0))
    jmap = np.array([names.index(_twin(nm)) if _twin(nm) in names else k for k, nm in enumerate(names)])

    new_at = {}
    for k, ai in at.items():
        A = G.get(ai)
        B = A[src_idx].copy()
        if k in ("POSITION", "NORMAL"):
            B[mir] = B[mir] * flip3
        elif k.startswith("JOINTS_"):
            B[mir] = jmap[B[mir].astype(np.int64)]
        elif k.startswith("TANGENT"):
            B[mir, 0] = -B[mir, 0]
            B[mir, 3] = -B[mir, 3]
        new_at[k] = _acc(G, B, ai, minmax=(k == "POSITION"))
    # triangles: the source's (renumbered), and the mirror's (winding flipped), in the old side order
    remap = np.full(n, -1, np.int64)
    remap[sv] = new_of_src
    Is = remap[I[st]]
    mremap = np.full(n, -1, np.int64)
    mremap[sv] = new_of_mir
    Im = mremap[I[st]][:, [0, 2, 1]]
    Inew = np.concatenate([Im, Is] if dst_first else [Is, Im])
    assert Inew.max() < 2 * ns
    ia = g["accessors"][p["indices"]]
    if 2 * ns > 65535 and ia["componentType"] == 5123:
        ia = dict(ia, componentType=5125)
    bv = _append(G, np.ascontiguousarray(Inew.ravel(), dtype=_CT[ia["componentType"]]).tobytes())
    g["accessors"].append({"bufferView": bv, "componentType": ia["componentType"], "count": int(Inew.size), "type": "SCALAR"})
    new_idx = len(g["accessors"]) - 1

    # morph targets
    tn = list((m.get("extras") or {}).get("targetNames", []))
    tg = p.get("targets", [])
    new_tg = []
    for ti, t in enumerate(tg):
        nm = tn[ti] if ti < len(tn) else None
        tw = tn.index(_twin(nm)) if nm is not None and _twin(nm) in tn else ti
        nt = {}
        for key, ai in t.items():
            own = _read_sparse(G, ai) if key in ("POSITION", "NORMAL") else G.get(ai).astype(np.float64)
            twin = _read_sparse(G, tg[tw][key]) if key in ("POSITION", "NORMAL") else G.get(tg[tw][key]).astype(np.float64)
            V = np.zeros((2 * ns, 3))
            V[new_of_src] = own[sv]
            V[new_of_mir] = twin[sv] * flip3
            if "sparse" in g["accessors"][ai]:
                nz = np.where(np.abs(V).max(1) > 0)[0]
                nt[key] = _sparse_g(G, 2 * ns, nz, V[nz])
            else:
                nt[key] = _acc(G, V, ai, minmax=True)
        new_tg.append(nt)

    # pieces (heroine_lod's slot join)
    ex = m.get("extras") or {}
    pcs = ex.get("pieces")
    if pcs:
        ntri, acc_t, out_s, out_d = 0, 0, [], []
        first_s = st[0]
        for place, cnt in pcs:
            r = (acc_t, acc_t + cnt)
            acc_t += cnt
            (out_s if r[0] >= first_s and r[1] <= st[-1] + 1 else out_d).append([place, cnt])
        assert sum(c for _, c in out_s) == len(st) and sum(c for _, c in out_d) == len(dt_), f"{m['name']}: pieces straddle the sides"
        if len(out_s) != len(out_d):
            assert pieces_free, f"{m['name']}: {len(out_d)} destination pieces vs {len(out_s)} source pieces"
        dplaces = [pl for pl, _ in out_d]
        mir_p = [[dplaces[min(i, len(dplaces) - 1)], c] for i, (_, c) in enumerate(out_s)]
        ex["pieces"] = (mir_p + out_s) if dst_first else (out_s + mir_p)

    old = dict(n=n, nd=len(dv), td=len(dt_))
    p["attributes"] = new_at
    p["indices"] = new_idx
    if new_tg:
        p["targets"] = new_tg
    return dict(name=m["name"], ns=ns, nd_old=old["nd"], td_old=old["td"], tris=len(st), dst_first=dst_first)


def mirror_records(path, body, src_right=True, dry=False):
    """A tuck/cover record file (u32 count; i32 x, y, z of her body's bind point x 1e5; f32 value) with its DST side
    rebuilt from its SRC side: each of her body's DST-side points takes the value of her SRC-side point nearest its
    mirror image (0: no record), the records' own values copied, not blended (her body is near-symmetric, ~2 mm). The
    SRC side's records are kept as they are, in their order; the mirror's follow, in her points' order."""
    from scipy.spatial import cKDTree
    from body_follow_post import Body, _rkey
    b = open(path, "rb").read()
    n = int(np.frombuffer(b[:4], "<u4")[0])
    rec = np.frombuffer(b, np.dtype([("k", "<i4", 3), ("v", "<f4")]), n, 4)
    B = body if isinstance(body, Body) else Body(body)
    U = B.U
    key = _rkey(U)
    at = {tuple(int(x) for x in k): i for i, k in enumerate(key)}
    sx = (lambda x: x < 0) if src_right else (lambda x: x > 0)
    keep = sx(rec["k"][:, 0])
    val = np.zeros(len(U))
    miss = 0
    for r in rec[keep]:
        i = at.get(tuple(int(x) for x in r["k"]))
        if i is None:
            miss += 1
        else:
            val[i] = r["v"]
    su = np.where(sx(U[:, 0]))[0]
    du = np.where(~sx(U[:, 0]) & (U[:, 0] != 0))[0]
    d, j = cKDTree(U[su]).query(U[du] * [-1, 1, 1])
    v = val[su[j]]
    on = v > 0
    new = np.zeros(int(keep.sum() + on.sum()), rec.dtype)
    new[:keep.sum()] = rec[keep]
    new["k"][keep.sum():] = key[du[on]]
    new["v"][keep.sum():] = v[on]
    print("MIRROR_REC %-44s kept %d %s records (%d not at her points), dropped %d, wrote %d mirrored (mirror pair gap median %.2f mm, max %.2f)"
          % (os.path.relpath(path), keep.sum(), "right" if src_right else "left", miss, (~keep).sum(), on.sum(),
             1000 * np.median(d[on]) if on.any() else 0, 1000 * d[on].max() if on.any() else 0))
    if not dry:
        open(path, "wb").write(np.uint32(len(new)).tobytes() + new.tobytes())
    return new


def main(argv):
    a = [x for x in argv if not x.startswith("--")]
    src_right = (argv[argv.index("--from") + 1] if "--from" in argv else "right") == "right"
    if "--records" in argv:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
        from body_follow_post import Body
        body = Body(argv[argv.index("--body") + 1])
        for f in argv[argv.index("--records") + 1].split(","):
            mirror_records(f, body, src_right, "--dry" in argv)
        return
    path = a[0]
    meshes = argv[argv.index("--meshes") + 1].split(",")
    assert path.endswith(".gltf"), "a .gltf with its .bin (a .glb's chunk header is not rewritten)"
    G = _Gl(path)
    for nm in meshes:
        mi = [i for i, m in enumerate(G.g["meshes"]) if m.get("name") == nm]
        assert len(mi) == 1, f"mesh {nm}: {len(mi)} found"
        r = mirror_mesh(G, mi[0], src_right, "--pieces-free" in argv)
        print("MIRROR %-26s %s side -> %s: %d source points/%d tris; the rebuilt side was %d points/%d tris"
              % (r["name"], "right" if src_right else "left", "left" if src_right else "right", r["ns"], r["tris"], r["nd_old"], r["td_old"]))
    G.g["buffers"][0]["byteLength"] = len(G.buf) - G.b0
    if "--dry" in argv:
        print("MIRROR dry: nothing written")
        return
    G.save()
    print("MIRROR wrote", path, "(%.2f MiB bin before compaction)" % ((len(G.buf) - G.b0) / 2 ** 20))


if __name__ == "__main__":
    main(sys.argv[1:])
