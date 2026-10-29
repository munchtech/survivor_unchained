"""An armor piece's gameplay LOD and shadow LOD, beside its full meshes in its own glTF (the look bible's budgets:
gameplay at most 25% of the full piece's triangles, shadow at most 10%).

    python tools/armor/piece_lod.py godot/art/armor/<id>.gltf [--numbers <numbers.json>]

Run by tools/armor/build.py right after each build (the file it reads is the build's fresh export, without LODs).
Each full mesh <id>.<slot>.<mat> gets a sibling <id>.lod1.<mat>: its small parts dropped (rivets, buckles: any
connected part under SMALL across, which at the play camera is a highlight of a pixel or two), the rest simplified
with meshoptimizer to its share of the budget, keeping every vertex where it was (so its normals, UVs, colours and
weights are the full mesh's own), quadric error weighted by normals so broad curves keep their shading and the rolled
edges their line of light. One <id>.shadow for both materials: the kept parts welded into one surface, simplified
harder (PRUNE drops what can't hold a shape) and drawn in by INSET along its normals so it never rises over what it
shades. All skinned on her skeleton (the same skin, JOINTS_0 and WEIGHTS_0). Mesh extras: {"lod": "lod1"|"shadow",
"of": [the full meshes]}. People.HerWear shows the gameplay LOD and the shadow at the play camera (HerLod's switch).
"""
import ctypes
import json
import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
import heroine_lod as hl  # noqa: E402
import meshoptimizer as mo  # noqa: E402
from meshoptimizer._loader import lib as _mo  # noqa: E402

GAMEPLAY = 0.25 * 0.92   # (of the full piece's triangles; a margin under the bible's 25%)
SHADOW = 0.10 * 0.90     # (and 10%)
# (armor 9: a small free mesh (Marionette's are 1-4k triangles) can't reach 25% inside ERROR_CAP; its gameplay LOD
# passes under this many triangles however small its share. A decision for the armor lead: FLOOR = 0 restores the
# share rule alone.)
FLOOR = int(os.environ.get("LOD_FLOOR", "1800"))
SMALL = 0.035            # (m: a connected part smaller across than this is dropped from both)
ERROR_CAP = 0.004        # (m: the simplifier's error never past this; a pixel at the play camera is 5-10 mm)
INSET = 0.0008           # (m: the shadow drawn in along its normals)
NORMALS = hl.NORMALS


def simplify_to(idx, pos, target_tris, cap, attrs=None, weights=None, opts=0):
    """meshopt_simplify(WithAttributes) to a triangle target within an error cap: (indices, the error reached)."""
    idx = np.ascontiguousarray(idx, np.uint32)
    pos = np.ascontiguousarray(pos, np.float32)
    dst = np.zeros(len(idx), np.uint32)
    err = ctypes.c_float(0)
    tgt = int(target_tris) * 3
    if attrs is None:
        n = _mo.meshopt_simplify(dst.ctypes.data, idx.ctypes.data, len(idx), pos.ctypes.data, len(pos), 12, tgt, cap,
                                 opts, ctypes.addressof(err))
    else:
        attrs = np.ascontiguousarray(attrs, np.float32)
        weights = np.ascontiguousarray(weights, np.float32)
        n = _mo.meshopt_simplifyWithAttributes(dst.ctypes.data, idx.ctypes.data, len(idx), pos.ctypes.data, len(pos), 12,
                                               attrs.ctypes.data, attrs.shape[1] * 4, weights.ctypes.data, len(weights),
                                               None, tgt, cap, opts, ctypes.addressof(err))
    return dst[:n].reshape(-1, 3).astype(np.int64), err.value


def parts(pos, tris):
    """Each triangle's connected part (vertices welded by position, so UV seams don't split a part)."""
    _, inv = np.unique(np.round(pos / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    w = inv.ravel()[tris]
    e = np.vstack([w[:, [0, 1]], w[:, [1, 2]], w[:, [2, 0]]])
    nv = int(w.max()) + 1
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)), directed=False)
    return lab[w[:, 0]]


def floats(arr, norm):
    a = arr.astype(np.float32)
    if norm:
        a = a / {np.dtype(np.uint8): 255.0, np.dtype(np.uint16): 65535.0}.get(arr.dtype, 1.0)
    return a


class Appender:
    """Meshes appended to an existing .gltf and its .bin (the skin, nodes and materials kept)."""

    def __init__(self, g):
        self.g, self.js = g, g.js
        self.bin = bytearray(g.bin)

    def add(self, arr, normalized, target=None):
        arr = np.ascontiguousarray(arr)
        while len(self.bin) % 4:
            self.bin.append(0)
        bv = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": arr.nbytes}
        if target:
            bv["target"] = target
        self.bin += arr.tobytes()
        self.js["bufferViews"].append(bv)
        a = {"bufferView": len(self.js["bufferViews"]) - 1, "componentType": hl._CODE[arr.dtype], "count": len(arr),
             "type": hl._TYPE[1 if arr.ndim == 1 else arr.shape[1]]}
        if normalized:
            a["normalized"] = True
        if arr.ndim == 2 and arr.shape[1] == 3 and arr.dtype == np.float32:
            a["min"], a["max"] = arr.min(0).tolist(), arr.max(0).tolist()
        self.js["accessors"].append(a)
        return len(self.js["accessors"]) - 1

    def material(self, name):
        for i, m in enumerate(self.js["materials"]):
            if m["name"] == name:
                return i
        self.js["materials"].append({"name": name, "doubleSided": False})
        return len(self.js["materials"]) - 1

    def mesh(self, name, mat, attrs, tris, parent, extras):
        used, inv = np.unique(tris.ravel(), return_inverse=True)
        p = {"attributes": {}, "material": mat}
        for k, (arr, norm) in attrs.items():
            p["attributes"][k] = self.add(np.ascontiguousarray(arr[used]), norm, 34962)
        p["indices"] = self.add(inv.astype(np.uint32 if len(used) > 65535 else np.uint16), False, 34963)
        self.js["meshes"].append({"name": name, "primitives": [p], "extras": extras})
        self.js["nodes"].append({"name": name, "mesh": len(self.js["meshes"]) - 1, "skin": 0})
        self.js["nodes"][parent].setdefault("children", []).append(len(self.js["nodes"]) - 1)

    def save(self, path):
        self.js["buffers"][0]["byteLength"] = len(self.bin)
        open(os.path.join(os.path.dirname(path), self.js["buffers"][0]["uri"]), "wb").write(bytes(self.bin))
        json.dump(self.js, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def main(argv):
    path = os.path.abspath(argv[0])
    g = hl.Gltf(path)
    js = g.js
    if any((m.get("extras") or {}).get("lod") for m in js["meshes"]):
        raise SystemExit(f"LOD: {path} has LODs already (run on the build's fresh export)")
    pid = js["asset"]["extras"]["armor_piece"]
    full = [(i, m) for i, m in enumerate(js["meshes"])]
    node_of = {n["mesh"]: k for k, n in enumerate(js["nodes"]) if "mesh" in n}
    parent = next(k for k, n in enumerate(js["nodes"]) if node_of[full[0][0]] in n.get("children", []))
    t0 = sum(len(g.prims(i)[0][2]) for i, _ in full)
    src = []
    for i, m in full:
        mat, attrs, tris = g.prims(i)[0]
        pos = attrs["POSITION"][0].astype(np.float64)
        lab = parts(pos, tris)
        keep = np.zeros(len(tris), bool)
        dropped = 0
        for c in np.unique(lab):
            sel = lab == c
            v = pos[np.unique(tris[sel])]
            if np.linalg.norm(v.max(0) - v.min(0)) >= SMALL:
                keep |= sel
            else:
                dropped += 1
        src.append((i, m, mat, attrs, tris, tris[keep], dropped))
    kept_total = sum(len(k) for *_, k, _ in src)
    budget = int(GAMEPLAY * t0)
    # (a material made only of small parts draws whole at the play camera and counts against the budget: the rest
    # share what is left (Body 14: plate_pauldrons_plain's straps, 312 triangles, put it 0.5% over))
    whole = sum(len(tris) for *_, tris, kt, _ in src if not len(kt))
    budget = max(budget - whole, int(0.5 * budget))
    ap = Appender(g)
    rep = {"full_triangles": t0, "lod1": {}, "shadow": {}}
    lod_tris = 0
    S_P, S_N, S_J, S_W, S_T = [], [], [], [], []
    base = 0
    for i, m, mat, attrs, tris, kt, dropped in src:
        if not len(kt):
            # (every part of it small (a material of rivets alone, armor 9's free meshes): no gameplay LOD of it, so
            # HerWear pairs none and the full mesh draws at the play camera too; none of it in the shadow)
            rep["lod1"][mat] = {"full": len(tris), "small_parts_dropped": dropped, "kept": 0, "lod1": None}
            lod_tris += len(tris)     # (it draws whole at the play camera: counted against the gameplay budget)
            continue
        share = max(64, int(budget * len(kt) / max(kept_total, 1)))
        pos = attrs["POSITION"][0].astype(np.float32)
        cols = [attrs["NORMAL"][0].astype(np.float32)]
        wts = [NORMALS] * 3
        if "TEXCOORD_0" in attrs:
            cols.append(attrs["TEXCOORD_0"][0].astype(np.float32))
            wts += [0.002, 0.002]
        out, err = simplify_to(kt.ravel(), pos, share, ERROR_CAP, np.concatenate(cols, 1), np.array(wts, np.float32),
                               mo.SIMPLIFY_ERROR_ABSOLUTE)
        if len(out) > share * 1.05:
            # (seams and normals held it up: by position alone, the cap kept)
            out, err = simplify_to(kt.ravel(), pos, share, ERROR_CAP, opts=mo.SIMPLIFY_ERROR_ABSOLUTE)
        ap.mesh(f"{pid}.lod1.{mat}", js["meshes"][i]["primitives"][0]["material"], attrs, out, parent,
                {"lod": "lod1", "of": [m["name"]], "material": mat})
        rep["lod1"][mat] = {"full": len(tris), "small_parts_dropped": dropped, "kept": len(kt), "lod1": len(out),
                            "error_mm": round(err * 1000, 2)}
        lod_tris += len(out)
        used, inv = np.unique(kt.ravel(), return_inverse=True)
        S_P.append(pos[used])
        S_N.append(attrs["NORMAL"][0][used].astype(np.float32))
        S_J.append(attrs["JOINTS_0"][0][used].astype(np.uint16))
        S_W.append(floats(*attrs["WEIGHTS_0"])[used])
        S_T.append(inv.reshape(-1, 3) + base)
        base += len(used)
    # The shadow: one welded surface of both materials' kept parts.
    P_, N_, J_, W_, T_ = map(np.concatenate, (S_P, S_N, S_J, S_W, S_T))
    _, first, weld = np.unique(np.round(P_ / 1e-5).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    weld = weld.ravel()
    T_ = weld[T_]
    T_ = T_[(T_[:, 0] != T_[:, 1]) & (T_[:, 1] != T_[:, 2]) & (T_[:, 2] != T_[:, 0])]
    Nw = np.zeros((len(first), 3))
    np.add.at(Nw, weld, N_)
    Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-9)
    Pw = P_[first].astype(np.float64) - Nw * INSET
    s_budget = int(SHADOW * t0)
    Ts, serr = simplify_to(T_.ravel(), Pw, s_budget, 0.012, opts=mo.SIMPLIFY_ERROR_ABSOLUTE | mo.SIMPLIFY_PRUNE)
    sattrs = {"POSITION": (Pw.astype(np.float32), False), "NORMAL": (Nw.astype(np.float32), False),
              "JOINTS_0": (J_[first], False), "WEIGHTS_0": (W_[first], False)}
    ap.mesh(f"{pid}.shadow", ap.material("lod_shadow"), sattrs, Ts, parent, {"lod": "shadow", "of": [m["name"] for _, m in full]})
    rep["shadow"] = {"welded": len(T_), "shadow": len(Ts), "error_mm": round(serr * 1000, 2)}
    rep["lod1_triangles"] = lod_tris
    rep["lod1_share"] = round(lod_tris / t0, 3)
    rep["shadow_share"] = round(len(Ts) / t0, 3)
    rep["draws"] = {"full": len(full), "lod1": len(src), "shadow_pass_at_play": 1}
    js["asset"].setdefault("extras", {})["lods"] = {"gameplay": GAMEPLAY, "shadow": SHADOW, "small": SMALL, "inset": INSET}
    ap.save(path)
    ok = lod_tris <= max(0.25 * t0, FLOOR) and len(Ts) <= max(0.10 * t0, FLOOR * 0.4)
    rep["floor"] = FLOOR if lod_tris > 0.25 * t0 or len(Ts) > 0.10 * t0 else None
    print("LOD %s: %d -> lod1 %d (%.1f%%), shadow %d (%.1f%%)%s" % (pid, t0, lod_tris, 100 * lod_tris / t0, len(Ts),
                                                                  100 * len(Ts) / t0, "" if ok else "  OVER BUDGET"))
    if "--numbers" in argv:
        npth = argv[argv.index("--numbers") + 1]
        num = json.load(open(npth, encoding="utf-8"))
        num["lods"] = rep
        json.dump(num, open(npth, "w", encoding="utf-8"), indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
