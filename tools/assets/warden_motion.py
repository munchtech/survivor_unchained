"""A package's pieces in motion, measured (Warden 6): each skinned piece (armor/*.glb, the hair file) skinned on the
game's own pose and its own bind, per clip: edge stretch against the bind, and its vertices inside the body.

    blender -b -P tools/assets/warden_motion.py -- PKG_DIR --pose DUMP.jsonl [--pose ...] [--collider BODY.glb]
        [--out OUT.json] [--every 2] [--obj FRAME OUT_DIR]

The poses are the game's (WARDEN_POSEDUMP=PATH on the Ford-Warden, BossViews.PoseDump): a header with each skinned
surface's bind names and poses, then each drawn frame's bone global poses. Frames are grouped by the clip sampled
(WARDEN_POSECLIPS) or else the clip the cinematic was playing. Each vertex is skinned as the GPU skins it: the
weighted sum of pose(bone) x bind(bone), with the binds Godot holds (the glb's inverse binds when a surface wasn't in
the dump). The body (the collider: the package's body.glb unless --collider names one, e.g. the pre-hood body with
no cut under the hood) is skinned on the same frame.

Per piece and material, per clip:
  stretch: each edge's length over its bind length (edges under 1 mm at the bind are left out: their ratio is noise);
           p99 and max, and where the max is (its vertex's heaviest bone).
  poke:    vertices more than 2 mm inside the body (behind the nearest body triangle's face), on the worst frame:
           count and the deepest, by the vertex's heaviest bone; and the same at the bind, so what motion adds shows.
--obj FRAME DIR writes that frame's posed pieces and body as OBJ (glTF frame) for a look in Blender.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warden_head import Glb  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

BODY_MATS = ("generated", "warden_face", "warden_patch", "skin", "skin_head")
POKE = 0.002
MIN_EDGE = 0.001


def m34(a):
    M = np.eye(4)
    M[:3, :] = np.array(a, float).reshape(3, 4)
    return M


def load_piece(path):
    """Per primitive: material, positions, faces, joints (names), weights; the glb's inverse binds by joint name."""
    g = Glb(path)
    j = g.j
    out = []
    ibm = {}
    for sk in j.get("skins", []):
        names = [j["nodes"][n].get("name", f"n{n}") for n in sk["joints"]]
        I = g.acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1) if "inverseBindMatrices" in sk else np.tile(np.eye(4), (len(names), 1, 1))
        for n, M in zip(names, I):
            ibm.setdefault(n, M)
    # (the piece's own hierarchy, by name: a bone the body lacks (a cape chain) rides its nearest ancestor, as
    #  NpcPackage.Rebind binds it in the game)
    par = {j["nodes"][c].get("name", f"n{c}"): n.get("name", f"n{i}") for i, n in enumerate(j["nodes"]) for c in n.get("children", [])}
    for ni, node in enumerate(j["nodes"]):
        if "mesh" not in node or "skin" not in node:
            continue
        names = [j["nodes"][n].get("name", f"n{n}") for n in j["skins"][node["skin"]]["joints"]]
        for p in j["meshes"][node["mesh"]]["primitives"]:
            a = p["attributes"]
            if "JOINTS_0" not in a:
                continue
            mat = j["materials"][p["material"]].get("name", "") if "material" in p else ""
            P = g.acc(a["POSITION"]).astype(float)
            F = g.acc(p["indices"]).reshape(-1, 3).astype(np.int64)
            J = g.acc(a["JOINTS_0"]).astype(np.int64)
            W = g.acc(a["WEIGHTS_0"]).astype(float)
            W /= W.sum(1, keepdims=True) + 1e-12
            out.append(dict(mesh=node.get("name", ""), mat=mat, P=P, F=F, J=J, W=W, names=names, par=par))
    return out, ibm


def read_dump(path):
    with open(path) as f:
        head = json.loads(f.readline())
        frames = []
        for l in f:
            try:
                frames.append(json.loads(l))
            except ValueError:
                pass   # (a line cut short when the game quit)
    return head, frames


class Skinner:
    def __init__(self, head):
        self.bi = {n: i for i, n in enumerate(head["bones"])}
        self.skins = head["skins"]
        self.rest = np.array([m34(x) for x in head["rest"]])

    def binds_for(self, prim, ibm):
        """The bind per joint of a primitive: the dumped skin listing its material (Godot's binds), else the glb's."""
        sk = next((s for s in self.skins if prim["mat"] in s["mats"]), None)
        if sk and len(sk["names"]) == len(prim["names"]):   # (Godot's binds, joint by joint: after a Rebind two joints may share a name)
            return np.array([m34(b) for b in sk["binds"]]), np.array([self.bi.get(n, 0) for n in sk["names"]]), True
        gb = {n: m34(b) for n, b in zip(sk["names"], sk["binds"])} if sk else {}
        par = prim.get("par", {})

        def anc(n):
            while n not in self.bi and n in par:
                n = par[n]
            return n
        names = [n if n in self.bi else anc(n) for n in prim["names"]]
        B = np.array([gb.get(n, ibm.get(n, np.eye(4))) for n in names])
        bone = np.array([self.bi.get(n, 0) for n in names])
        return B, bone, sk is not None

    @staticmethod
    def skin(prim, B, bone, pose):
        M = pose[bone] @ B                          # per joint
        Mv = np.einsum("nk,nkij->nij", prim["W"], M[prim["J"]])
        return np.einsum("nij,nj->ni", Mv[:, :3, :3], prim["P"]) + Mv[:, :3, 3]


def edges_of(F):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E.sort(1)
    return np.unique(E, axis=0)


def poke(Q, body_V, body_F, tree=None):
    """Depth (m) of each point behind the nearest body face (positive: inside)."""
    t = tree or BVHTree.FromPolygons([tuple(v) for v in body_V], [tuple(f) for f in body_F], all_triangles=True)
    d = np.zeros(len(Q))
    for i, q in enumerate(Q):
        loc, n, _, dist = t.find_nearest(tuple(q), 0.25)
        if loc is None:
            continue
        d[i] = float(np.dot(np.array(loc) - q, np.array(n)))
    return d, t


def write_obj(path, V, F):
    with open(path, "w") as f:
        for v in V:
            f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
        for t in F:
            f.write(f"f {t[0] + 1} {t[1] + 1} {t[2] + 1}\n")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    pkg = argv[0]
    poses = [argv[i + 1] for i, a in enumerate(argv) if a == "--pose"]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    every = int(opt("--every", "2"))
    collider = opt("--collider", os.path.join(pkg, "body.glb"))
    obj = (int(argv[argv.index("--obj") + 1]), argv[argv.index("--obj") + 2]) if "--obj" in argv else None
    man = json.load(open(os.path.join(pkg, "manifest.json")))
    files = [os.path.join("armor", f) for f in sorted(os.listdir(os.path.join(pkg, "armor"))) if f.endswith(".glb")] if os.path.isdir(os.path.join(pkg, "armor")) else []
    if man.get("hair", {}).get("file"):
        files.append(man["hair"]["file"])
    pieces = {f: load_piece(os.path.join(pkg, f)) for f in files}
    body_prims, body_ibm = load_piece(collider)
    body_prims = [p for p in body_prims if p["mat"] in BODY_MATS]
    report = {"package": pkg, "collider": collider, "dumps": poses, "pieces": {}}

    for dump in poses:
        head, frames = read_dump(dump)
        S = Skinner(head)
        frames = [f for k, f in enumerate(frames) if f["clip"] or k % every == 0]
        groups = {}
        for f in frames:
            groups.setdefault(f["clip"] or ("cine:" + (f["anim"] or "-")), []).append(f)
        bb = [S.binds_for(p, body_ibm) for p in body_prims]
        offs = np.cumsum([0] + [len(p["P"]) for p in body_prims])
        BF = np.concatenate([p["F"] + o for p, o in zip(body_prims, offs)])
        BV0 = np.concatenate([p["P"] for p in body_prims])
        # the bind check: the body skinned at the skeleton's rest against its own positions
        restV = np.concatenate([Skinner.skin(p, B, bo, S.rest) for p, (B, bo, _) in zip(body_prims, bb)])
        report.setdefault("restCheckMm", {})[os.path.basename(dump)] = round(float(np.abs(restV - BV0).max() * 1000), 2)
        print(f"[motion] {os.path.basename(dump)}: {len(frames)} frames, {len(groups)} clips; body at the skeleton's rest vs its bind: max {np.abs(restV - BV0).max() * 1000:.2f} mm")
        bind_tree = BVHTree.FromPolygons([tuple(v) for v in BV0], [tuple(f) for f in BF], all_triangles=True)
        work = []
        for fname, (prims, ibm) in pieces.items():
            for p in prims:
                B, bone, godot = S.binds_for(p, ibm)
                E = edges_of(p["F"])
                L0 = np.linalg.norm(p["P"][E[:, 0]] - p["P"][E[:, 1]], axis=1)
                keep = L0 >= MIN_EDGE
                top = np.array(p["names"])[p["J"][np.arange(len(p["P"])), np.argmax(p["W"], 1)]]
                d0, _ = poke(p["P"], BV0, BF, bind_tree)
                key = f"{fname}:{p['mat']}"
                rp = report["pieces"].setdefault(key, {"verts": len(p["P"]), "edges": int(keep.sum()), "edgesUnder1mm": int((~keep).sum()),
                                                       "bindsFrom": "godot" if godot else "glb",
                                                       "bindPoke": {"count": int((d0 > POKE).sum()), "maxMm": round(float(d0.max() * 1000), 1)}, "clips": {}})
                work.append(dict(p=p, B=B, bone=bone, E=E[keep], L0=L0[keep], top=top, d0=d0, key=key, rp=rp, fname=fname))
        for gname, fr in groups.items():
            acc = [dict(smax=0.0, s99=[], wmax="", worst=None) for _ in work]
            for f in fr:
                pose = np.array([m34(x) for x in f["pose"]])
                BV = np.concatenate([Skinner.skin(bp, Bb, bob, pose) for bp, (Bb, bob, _) in zip(body_prims, bb)])
                tree = BVHTree.FromPolygons([tuple(v) for v in BV], [tuple(t) for t in BF], all_triangles=True)
                if obj and f["frame"] == obj[0]:
                    os.makedirs(obj[1], exist_ok=True)
                    write_obj(os.path.join(obj[1], f"body_{f['frame']}.obj"), BV, BF)
                for w, a in zip(work, acc):
                    p, E = w["p"], w["E"]
                    V = Skinner.skin(p, w["B"], w["bone"], pose)
                    r = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1) / w["L0"]
                    a["s99"].append(np.percentile(r, 99))
                    if r.max() > a["smax"]:
                        a["smax"], a["wmax"] = float(r.max()), str(w["top"][E[np.argmax(r), 0]])
                    d, _ = poke(V, BV, BF, tree)
                    new = d > POKE
                    c = int(new.sum())
                    if a["worst"] is None or c > a["worst"][0]:
                        reg = {}
                        for t_ in w["top"][new]:
                            reg[t_] = reg.get(t_, 0) + 1
                        a["worst"] = (c, float(d.max()), f["frame"], dict(sorted(reg.items(), key=lambda x: -x[1])[:5]), int((new & ~(w["d0"] > POKE)).sum()))
                    if obj and f["frame"] == obj[0]:
                        write_obj(os.path.join(obj[1], f"{os.path.basename(w['fname'])}_{p['mat']}_{f['frame']}.obj"), V, p["F"])
            for w, a in zip(work, acc):
                wo = a["worst"]
                c = w["rp"]["clips"][gname] = {"frames": len(fr), "stretchP99": round(float(np.max(a["s99"])), 3), "stretchMax": round(a["smax"], 3), "maxAt": a["wmax"],
                                               "poke": {"count": wo[0], "notAtBind": wo[4], "maxMm": round(wo[1] * 1000, 1), "frame": wo[2], "by": wo[3]}}
                print(f"[motion] {w['key']:38s} {gname:30s} n={len(fr):4d} stretch p99 {c['stretchP99']:.3f} max {c['stretchMax']:.3f} ({a['wmax']}) "
                      f"poke {wo[0]} (+{wo[4]} vs bind) max {c['poke']['maxMm']} mm @f{wo[2]} {wo[3]}", flush=True)
    out = opt("--out")
    if out:
        json.dump(report, open(out, "w"), indent=1)
        print(f"[motion] wrote {out}")


main()
