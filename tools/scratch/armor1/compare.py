# compare.py REF NEW [--lod]: heroine.glb data-equal; each outfit's slot meshes vs its old per-material meshes; LOD files.
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
from heroine_lod import Gltf, slot_join

ref, new = sys.argv[1], sys.argv[2]
ATT = ["POSITION", "NORMAL", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0", "COLOR_0"]


def f(a):
    arr, norm = a
    if norm and arr.dtype.kind in "ui":
        return arr.astype(np.float64) / np.iinfo(arr.dtype).max
    return arr.astype(np.float64)


def meshes(g):
    out = {}
    for n in g.js["nodes"]:
        if "mesh" in n:
            out[n["name"]] = (n["mesh"], g.js["meshes"][n["mesh"]])
    return out


def cmp_prims(tag, pa, pb):
    bad = []
    (ma, aa, ta), (mb, ab, tb) = pa, pb
    if ma != mb or len(aa["POSITION"][0]) != len(ab["POSITION"][0]) or len(ta) != len(tb):
        return ["%s: material %s/%s, %d/%d vertices, %d/%d tris" % (tag, ma, mb, len(aa["POSITION"][0]), len(ab["POSITION"][0]), len(ta), len(tb))]
    for k in sorted(set(aa) | set(ab)):
        if k not in aa or k not in ab:
            bad.append("%s %s only in one" % (tag, k)); continue
        d = np.abs(f(aa[k]) - f(ab[k])).max() if len(aa[k][0]) else 0
        tol = {"COLOR_0": 1 / 255 + 1e-9, "TEXCOORD_0": 2e-6}.get(k, 1e-6)
        if d > tol:
            bad.append("%s %s max diff %.3g" % (tag, k, d))
    if not np.array_equal(ta, tb):
        same = np.array_equal(np.sort(np.sort(ta, 1), 0), np.sort(np.sort(tb, 1), 0))
        bad.append("%s indices differ (%d tris; as sets %s)" % (tag, int((ta != tb).any(1).sum()), "equal" if same else "DIFFERENT"))
    return bad


# 1. her body
ga, gb = Gltf(os.path.join(ref, "heroine.glb")), Gltf(os.path.join(new, "heroine.glb"))
ma, mb = meshes(ga), meshes(gb)
print("BODY meshes", sorted(ma) == sorted(mb), len(ma))
nb = 0
for name in sorted(ma):
    pa, pb = ga.prims(ma[name][0]), gb.prims(mb[name][0])
    for i, (x, y) in enumerate(zip(pa, pb)):
        for b in cmp_prims("body %s/%d" % (name, i), x, y):
            print("  ", b); nb += 1
print("BODY differences:", nb)

# 2. outfits
for o in ["warden", "arcanist", "ranger", "reaver"]:
    fa, fb = os.path.join(ref, f"heroine_outfit_{o}.gltf"), os.path.join(new, f"heroine_outfit_{o}.gltf")
    if not os.path.exists(fb):
        continue
    A, B = Gltf(fa), Gltf(fb)
    old = {A.prims(i)[0][0]: A.prims(i)[0] for i in range(len(A.js["meshes"]))}
    grp = {}
    for i, m in enumerate(B.js["meshes"]):
        for p in B.prims(i):
            grp.setdefault(p[0], []).append((m.get("extras", {}), p[1], p[2]))
    print("OUTFIT %s: %d old meshes, %d new (%s)" % (o, len(old), len(B.js["meshes"]), ", ".join(sorted(m["name"] for m in B.js["meshes"]))[:2000]))
    exact = 0
    for mat in sorted(set(old) | set(grp)):
        if mat not in old or mat not in grp:
            print("   %s only in one" % mat); continue
        got = grp[mat]
        attrs, tt = slot_join(got, mat)
        cat = (mat, attrs, tt)
        b = cmp_prims("%s.%s" % (o, mat), old[mat], cat)
        a0 = old[mat][1]
        nv = len(a0["POSITION"][0]) == len(attrs["POSITION"][0])
        def rows(a):
            return np.round(np.hstack([f(a["POSITION"]), f(a["JOINTS_0"]), f(a["WEIGHTS_0"])]), 5)
        if nv:
            ra, rb = rows(a0), rows(attrs)
            sa, sb = ra[np.lexsort(ra.T[::-1])], rb[np.lexsort(rb.T[::-1])]
            ok_sorted = np.abs(sa - sb).max() < 2e-5
        else:
            ok_sorted = False
        if b:
            print("   %s: %d slot meshes; vertices %s; sorted positions+weights %s; in order: %s" % (mat, len(got), "equal" if nv else "DIFFER", "equal" if ok_sorted else "DIFFER", "; ".join(b)))
        else:
            exact += 1
    print("   %d of %d materials identical in rank order (sorted rows checked where not)" % (exact, len(set(old) | set(grp))))

# 3. LOD
for o in ["warden", "arcanist", "ranger", "reaver"]:
    fa, fb = os.path.join(ref, f"heroine_outfit_{o}_lod.gltf"), os.path.join(new, f"heroine_outfit_{o}_lod.gltf")
    if not (os.path.exists(fa) and os.path.exists(fb)):
        continue
    A, B = Gltf(fa), Gltf(fb)
    ma_, mb_ = {m["name"]: i for i, m in enumerate(A.js["meshes"])}, {m["name"]: i for i, m in enumerate(B.js["meshes"])}
    nd = 0
    for n in sorted(set(ma_) | set(mb_)):
        if n not in ma_ or n not in mb_:
            print("   LOD %s %s only in one" % (o, n)); nd += 1; continue
        for i, (x, y) in enumerate(zip(A.prims(ma_[n]), B.prims(mb_[n]))):
            for b in cmp_prims("lod %s %s/%d" % (o, n, i), x, y):
                print("  ", b); nd += 1
    print("LOD %s: %d meshes, %d differences" % (o, len(ma_), nd))
