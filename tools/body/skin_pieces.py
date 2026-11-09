"""Skin-tight outfit pieces carried onto B (P1 R1 round 29; spec "pieces").

A's skin-tight slot pieces (the ink slot: reaver.ink, A's zigzag tattoos, a navy cloth decal 1.2-1.4 mm off A's skin)
are cut on A's surface; B could not wear them (P1Laws leaves A's outfit meshes off B). Here each piece's vertex is
carried by its surface point: its closest point on A's rest skin (triangle + barycentrics) and its offset from it
(the vector, in A's skin frame there); that point on A as the maps carry poses A into B's rest (her_a_target.a_source:
the fit's bones, her_a's a_rest chain), then its closest point on B's rest body; the vertex is B's point plus the
offset turned by the least rotation from A's skin normal to B's there; its normal and the piece's other attributes
likewise. It is skinned with B's weights at that point (the triangle's, barycentric, top 8) and carries B's blend
shapes (the correctives, the springs' support shapes) at that point, so it rides B's skin as A's rides A's.

Writes <build>/pieces.glb (B's skeleton as body.glb's, one mesh node per piece, its A node's name with dots made
underscores as Godot imports them; play-tier pieces onto play.glb's body) and <build>/pieces.json (each piece's A
file and node, its vertex count, the tier it rides, and the gates: offset to B's skin against A's, carry residual).
P1Body swaps A's node's mesh and skin for B's (A's node, materials and slot rules kept).

    python tools/body/skin_pieces.py <build_out> [--spec tools/body/specs/her_b.json]
"""
import argparse
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import glbwrite  # noqa: E402
from gl import Glb  # noqa: E402
from surfdist import Surface  # noqa: E402

PEOPLE = os.path.join(REPO, "godot", "art", "people")
A_PATH = os.path.join(PEOPLE, "heroine.glb")
INDEX = os.path.join(PEOPLE, "armor_index.json")


def U(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    w = np.clip(np.stack([1 - v - w, v, w], 1), 0, None)
    return w / w.sum(1, keepdims=True)


def least_rot(a, b):
    """[n,3,3] rotations taking unit a onto unit b by the least turn (Rodrigues)."""
    v = np.cross(a, b)
    c = (a * b).sum(1)
    K = np.zeros((len(a), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 0] = -v[:, 2], v[:, 1], v[:, 2]
    K[:, 1, 2], K[:, 2, 0], K[:, 2, 1] = -v[:, 0], -v[:, 1], v[:, 0]
    k = 1.0 / np.maximum(1.0 + c, 1e-9)
    return np.eye(3)[None] + K + np.einsum("nij,njk->nik", K, K) * k[:, None, None]


def pieces_of(cfg):
    """[(a_file, a_node, tier)]: every row of the armor index in cfg's slots (its meshes, close tier) and each of their
    outfits' gameplay file's lod_<material> mesh (play tier: HerLod's stand-in for the slot's material)."""
    with open(INDEX) as f:
        ix = json.load(f)
    rows = ix["pieces"] if isinstance(ix, dict) else ix
    rows = rows.values() if isinstance(rows, dict) else rows
    out = []
    for r in rows:
        if r.get("slot") not in cfg.get("slots", ["ink"]):
            continue
        f = r.get("file") or f"heroine_outfit_{r['outfit']}.gltf"
        for m in r["meshes"]:
            out.append((f, m, "close"))
            lod = f"heroine_outfit_{r['outfit']}_lod.gltf"
            if cfg.get("play", True) and os.path.exists(os.path.join(PEOPLE, lod)):
                key = ("lod_" + m.rsplit(".", 1)[-1])
                if (lod, key, "play") not in out:
                    out.append((lod, key, "play"))
    return out


def a_rest_points(g, mesh):
    """A piece's points at A's rest (skinned by its file's inverse binds and joint rests; A's outfits are bound at
    rest, so this is its stored points to float precision)."""
    sk = g.js["skins"][mesh.skin]
    ibm = g.acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)
    M = np.stack([g.world(j) for j in sk["joints"]]) @ ibm
    P = np.c_[mesh.P.astype(np.float64), np.ones(len(mesh.P))]
    W = mesh.W / np.maximum(mesh.W.sum(1, keepdims=True), 1e-12)
    X = np.einsum("nk,nkij,nj->ni", W, M[mesh.J], P)[:, :3]
    return X


class Target:
    """B's body (a tier's glb "Heroine") with its weights (dense by triangle corner) and blend shapes."""

    def __init__(self, path):
        self.path = path
        g = Glb(path)
        m = g.mesh("Heroine")
        self.P = m.P.astype(np.float64)
        self.N = U(m.N.astype(np.float64))
        self.T = m.T
        self.J, self.W = m.J, m.W
        self.surf = Surface(self.P, self.T)
        self.targets = glbwrite.get_targets(path, "Heroine")
        self.js, self.bin = glbwrite._read_glb(path)

    def use_ref(self, build_out, tier="close"):
        """P1 R1 sliders: a build laid from a ref body (build_topo target_joints_ref: stage/ref_rest_close.npy, the ref's
        rest in topology order; close.npz "src" maps this glb's vertices to it) finds A's point on the REF body (where
        A's maps carry it: the ref is the body her_a's fit was made on) and takes that triangle and barycentrics on
        this body: carried by vertex, as weights_topo.a_lookup carries A's patches. On a height or hips slider the
        nearest point of this body to A's point lay 9-77 mm off, on the wrong part (the hip's ink on pelvis weights)."""
        st = os.path.join(build_out, "stage")
        rp, zp = os.path.join(st, f"ref_rest_{tier}.npy"), os.path.join(st, f"{tier}.npz")
        if not (os.path.exists(rp) and os.path.exists(zp)):
            return False
        z = np.load(zp)
        src = z["src"]
        if len(src) != len(self.P) or np.abs(z["V"][src] - self.P).max() > 1e-5:
            print("skin_pieces: the build's topology map does not match its body.glb; nearest-point carry")
            return False
        self.Pref = np.load(rp)[src].astype(np.float64)
        self.surf_ref = Surface(self.Pref, self.T)
        return True

    def at(self, X):
        if getattr(self, "surf_ref", None) is not None:
            qr, _, t, d = self.surf_ref.closest(X, k=16)
            Tv = self.T[t]
            w = bary(qr, *(self.Pref[Tv[:, k]] for k in range(3)))
            q = (w[:, :, None] * self.P[Tv]).sum(1)
            n = U((w[:, :, None] * self.N[Tv]).sum(1))
            return q, n, Tv, w, d
        q, _, t, d = self.surf.closest(X, k=16)
        Tv = self.T[t]
        w = bary(q, *(self.P[Tv[:, k]] for k in range(3)))
        n = U((w[:, :, None] * self.N[Tv]).sum(1))
        return q, n, Tv, w, d

    def weights(self, Tv, w, k=8):
        n = len(Tv)
        J = self.J[Tv].reshape(n, -1)                       # [n, 3*K]
        W = (self.W[Tv] * w[:, :, None]).reshape(n, -1)
        Jo = np.zeros((n, k), np.int64)
        Wo = np.zeros((n, k))
        for i in range(n):
            acc = {}
            for j, x in zip(J[i], W[i]):
                if x > 0:
                    acc[int(j)] = acc.get(int(j), 0.0) + float(x)
            top = sorted(acc.items(), key=lambda kv: -kv[1])[:k]
            s = sum(x for _, x in top)
            for c, (j, x) in enumerate(top):
                Jo[i, c], Wo[i, c] = j, x / s
        return Jo, Wo


def carry(src_a, A_rest, a_surf, piece_g, piece, tgt):
    """One piece onto a target: (attributes, report)."""
    X = a_rest_points(piece_g, piece)
    qa, _, ta, da = a_surf.closest(X, k=16)
    Ta = A_rest["T"][ta]
    wa = bary(qa, *(A_rest["P"][Ta[:, k]] for k in range(3)))
    na = U((wa[:, :, None] * A_rest["N"][Ta]).sum(1))
    off = X - qa
    sgn = np.sign((off * na).sum(1))
    qp = (wa[:, :, None] * src_a.P[Ta]).sum(1)              # A's point as the maps carry poses A (B's rest)
    qb, nb, Tb, wb, resid = tgt.at(qp)
    R = least_rot(na, nb)
    Xb = qb + np.einsum("nij,nj->ni", R, off)
    Nb = U(np.einsum("nij,nj->ni", R, piece.N.astype(np.float64)))
    J, W = tgt.weights(Tb, wb)
    shapes = {}
    for nm, (dP, dN) in tgt.targets.items():
        sP = (wb[:, :, None] * dP.astype(np.float64)[Tb]).sum(1)
        if np.abs(sP).max() < 1e-7:
            continue
        shapes[nm] = sP
    # gates: the piece's offset to B's skin (closest, signed) against its offset to A's
    q2, fn2, _, db = tgt.surf.closest(Xb, k=16)
    sb = np.sign(((Xb - q2) * fn2).sum(1))
    pc = lambda x: [round(float(v), 3) for v in np.percentile(x * 1000, [5, 50, 95, 100])]  # noqa: E731
    rep = {"verts": int(len(X)), "a_offset_mm_p5_50_95_max": pc(da), "a_below": int((sgn < 0).sum()),
           "b_offset_mm_p5_50_95_max": pc(db), "b_below": int((sb < 0).sum()),
           "offset_change_mm_p50_95_max": [round(float(v), 3) for v in np.percentile(np.abs(db - da) * 1000, [50, 95, 100])],
           "carry_residual_mm_p50_95_max": [round(float(v), 3) for v in np.percentile(resid * 1000, [50, 95, 100])],
           "shapes": sorted(shapes)}
    return {"P": Xb, "N": Nb, "J": J, "W": W, "shapes": shapes}, rep


def write(path, ref, items):
    """pieces.glb: ref's (body.glb's) joint nodes and skin verbatim; one mesh node per item (its own primitive's
    attributes from the piece's file, POSITION/NORMAL/JOINTS/WEIGHTS ours, morph targets ours)."""
    rjs, rbin = glbwrite._read_glb(ref)
    out = glbwrite._Out()
    sk = rjs["skins"][0]
    nj = len(sk["joints"])
    assert sk["joints"] == list(range(nj)), "body.glb's joints are not its first nodes"
    nodes = [dict(rjs["nodes"][j]) for j in range(nj)]
    for n in nodes:
        n["children"] = [c for c in n.get("children", []) if c < nj]
        if not n["children"]:
            n.pop("children")
    skin = {"name": "Armature", "joints": list(range(nj)), "inverseBindMatrices": out.copy_acc(rjs, rbin, sk["inverseBindMatrices"])}
    meshes, mesh_nodes = [], []
    mats = [{"name": "p1_piece", "pbrMetallicRoughness": {"baseColorFactor": [0.2, 0.25, 0.35, 1.0]}, "doubleSided": True}]
    for it in items:
        g, pr, c = it["g"], it["prim"], it["carried"]
        att = {}
        for k, ai in pr["attributes"].items():
            if k == "POSITION":
                att[k] = out.acc(c["P"].astype(np.float32), "VEC3", 5126, 34962, minmax=True)
            elif k == "NORMAL":
                att[k] = out.acc(c["N"].astype(np.float32), "VEC3", 5126, 34962)
            elif k.startswith(("JOINTS_", "WEIGHTS_", "TANGENT")):
                continue
            else:
                att[k] = out.acc(g.acc(ai), g.js["accessors"][ai]["type"], g.js["accessors"][ai]["componentType"], 34962,
                                 normalized=g.js["accessors"][ai].get("normalized", False))
        for s in range(2):
            att[f"JOINTS_{s}"] = out.acc(c["J"][:, 4 * s:4 * s + 4], "VEC4", 5123, 34962)
            att[f"WEIGHTS_{s}"] = out.acc(c["W"][:, 4 * s:4 * s + 4], "VEC4", 5126, 34962)
        idx = g.acc(pr["indices"]).astype(np.uint32).reshape(-1)
        p = {"attributes": att, "indices": out.acc(idx, "SCALAR", 5125, 34963), "material": 0}
        names = sorted(c["shapes"])
        if names:
            p["targets"] = [{"POSITION": out.acc(c["shapes"][n].astype(np.float32), "VEC3", 5126, 34962, minmax=True)} for n in names]
        meshes.append({"name": it["name"], "primitives": [p], "extras": {"targetNames": names}, "weights": [0.0] * len(names)})
        mesh_nodes.append({"name": it["name"], "mesh": len(meshes) - 1, "skin": 0})
    base = len(nodes)
    nodes += mesh_nodes
    roots = [j for j in range(nj) if not any(j in n.get("children", []) for n in nodes[:nj])]
    nodes.append({"name": "Armature", "children": list(range(base, base + len(mesh_nodes))) + roots})
    js = {"asset": {"generator": "Survivor Unchained tools/body/skin_pieces.py", "version": "2.0"}, "scene": 0,
          "scenes": [{"name": "Scene", "nodes": [len(nodes) - 1]}], "nodes": nodes, "meshes": meshes, "materials": mats,
          "skins": [skin], "accessors": out.accs, "bufferViews": out.views, "buffers": [{"byteLength": 0}]}
    while len(out.bin) % 4:
        out.bin += b"\0"
    js["buffers"][0]["byteLength"] = len(out.bin)
    j = json.dumps(js, separators=(",", ":")).encode()
    j += b" " * ((4 - len(j) % 4) % 4)
    blob = (struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(out.bin)) + struct.pack("<II", len(j), 0x4E4F534A)
            + j + struct.pack("<II", len(out.bin), 0x004E4942) + bytes(out.bin))
    with open(path, "wb") as f:
        f.write(blob)


def run(build_out, spec):
    import her_a_target
    from sliders import load_spec
    cfg = spec.get("pieces") or {}
    ha = spec["her_a"]
    fit = load_spec(os.path.join(REPO, ha["fit_spec"]))
    src_a = her_a_target.a_source(ha, fit)
    am = Glb(A_PATH).mesh("Heroine")
    A_rest = {"P": am.P.astype(np.float64), "N": U(am.N.astype(np.float64)), "T": am.T}
    a_surf = Surface(A_rest["P"], am.T)
    assert len(src_a.P) == len(am.P), "the maps' posed A is not A's file order"
    tgts = {"close": Target(os.path.join(build_out, "body.glb"))}
    if os.path.exists(os.path.join(build_out, "play.glb")):
        tgts["play"] = Target(os.path.join(build_out, "play.glb"))
    by_ref = {k: t.use_ref(build_out, k) for k, t in tgts.items()}
    files, items, rep = {}, [], {"slots": cfg.get("slots", ["ink"]), "pieces": {}, "carried_by_ref": by_ref}
    for f, node, tier in pieces_of(cfg):
        if tier not in tgts:
            continue
        g = files.setdefault(f, Glb(os.path.join(PEOPLE, f)))
        m = g.mesh(node)
        if m is None:
            rep["pieces"][node] = {"file": f, "missing": True}
            continue
        nd = next(n for n in g.nodes if n.get("name") == node)
        prims = g.js["meshes"][nd["mesh"]]["primitives"]
        assert len(prims) == 1, f"{node}: one primitive expected"
        c, r = carry(src_a, A_rest, a_surf, g, m, tgts[tier])
        name = (f[len("heroine_outfit_"):-len(".gltf")] + "__" if tier == "play" else "") + node.replace(".", "_")
        r.update({"a_file": f, "a_node": node, "a_godot_name": node.replace(".", "_"), "tier": tier})
        rep["pieces"][name] = r
        items.append({"name": name, "g": g, "prim": prims[0], "carried": c, "tier": tier})
    if not items:
        return rep
    write(os.path.join(build_out, "pieces.glb"), os.path.join(build_out, "body.glb"), items)
    with open(os.path.join(build_out, "pieces.json"), "w") as f:
        json.dump(rep, f, indent=1)
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build_out")
    ap.add_argument("--spec", default=os.path.join(HERE, "specs", "her_b.json"))
    a = ap.parse_args()
    from sliders import load_spec
    rep = run(os.path.abspath(a.build_out), load_spec(a.spec))
    for k, v in rep["pieces"].items():
        print(k, {x: v[x] for x in v if x != "shapes"}, len(v.get("shapes", [])), "shapes")


if __name__ == "__main__":
    main()
