"""Base-native gear (P2): a piece authored directly on her_b (body B, godot/art/people/body_p1) bound as it stands.

The other 44 units were made on body A and are carried to B by `gear_fit bind`. A native piece is modelled at B's REST,
so its bind is the identity: every vertex is bound where it is, to the base topology (or her head), and from there
`gear_fit build --body <any body>` fits it like every other unit (bendy parts by the field, rigid parts made to
measure), `gear_fit stale` covers it, and the index row is its piece.json. A new armor piece is data: a piece dir.

A piece dir (godot/art/gear/native/<id>/):
    piece.json   id, name, slot, style, tier, layer, covers, optional hair ("hide"), dye zones,
                 "native": {"rest_body": "godot/art/people/body_p1", "rest_hash": {"close": sha1, "play": sha1}},
                 "parts": {part name: {"ride": {role: share}, "one_bone": bool} | {"bones": {bone: share}}
                           | {"with": part name}}   ("bones": the blend named bone by bone, "{s}" = the part's side:
                           an articulated lame rides exactly the bones its skin follows, e.g. thigh_twist_02_{s} 0.9
                           + calf_share_{s} 0.1, and none of her corrective shapes: part_blends; with "carry": "part"
                           it takes her arm_hang_* and elbow_* shapes as ONE rigid motion of the whole part;
                           "bend": {"max", "smooth", "clear", "clips"} on such a part: it bends only as far as her
                           moving skin needs, part_blends' alpha solve)
    <id>.glb     one node per part and material, at her_b's rest (glTF axes, metres, identity transforms), each a single
                 primitive whose material NAME is an entry of godot/art/people/outfit_materials.json. A part named
                 `*_rigid` never bends: it rides one blend of bones, its "ride" rule (roles as tools/armor/
                 rigid_roles.json "roles"), or the part it is fixed to ("with": rivets ride their plate). Other parts
                 follow her skin.
    <id>.sockets.json (optional)  sockets and rims as the armor pieces have them.

`validate` refuses a bad dir with plain reasons (no rest stamp or another body's, unknown material, a `_rigid` part
with no role, node transforms, open scalp under a hair-hiding helm). `bind` writes godot/art/gear/bind/<id>.npz (the
same arrays as gear_fit's) and <id>.src.glb beside it (the parts merged per material: what the build reads UVs,
indices and materials from; a build output).

gear_fit.py loads this module through one hook (`install`): its units() also lists the native dirs, bind_unit sends
them here, stale_units also sees a changed piece.json, and eval_unit gives each rigid part its own ride rule.

    python tools/armor/gear_native.py validate godot/art/gear/native/<id>
    python tools/armor/gear_native.py bind godot/art/gear/native/<id>
    python tools/armor/gear_fit.py build --body godot/art/people/body_p1 --only <id> [--out dir]
"""
import json
import os
import re
import struct
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
NATIVE = os.path.join(REPO, "godot", "art", "gear", "native")
MATERIALS = os.path.join(REPO, "godot", "art", "people", "outfit_materials.json")
SCALP = os.path.join(NATIVE, "scalp_mask.json")
SLOTS = ("top", "bottom", "legwear", "gloves", "skirt", "belt", "collar", "bracers", "greaves", "boots", "pauldrons",
         "cloak", "head")
LAYER = {"pauldrons": 3, "cloak": 3, "head": 3, "belt": 2, "bracers": 2, "greaves": 2, "boots": 2}
SCALP_COVER_M = 0.015   # a scalp point is covered when the helm lies within this, outward of it
_GF = None


def gf():
    global _GF
    if _GF is None:
        sys.path.insert(0, HERE)
        import gear_fit
        _GF = gear_fit
    return _GF


def rel(p):
    return os.path.relpath(p, REPO).replace("\\", "/")


# ---------------------------------------------------------------- glb in and out (a piece's own small files)

def write_glb(path, nodes, extras=None, materials=None, tail=None):
    """nodes: [{name, P, N, T, uv0, uv1, col, material, extras}] -> a .glb (one primitive a node; materials by name,
    or `materials`: ready glTF material dicts by name; `tail`: extra top-level keys such as textures and images)."""
    acc, views, blob, mats, meshes, out_nodes = [], [], bytearray(), [], [], []

    def put(a, typ, ct, target=None, minmax=False):
        a = np.ascontiguousarray(a)
        while len(blob) % 4:
            blob.append(0)
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": a.nbytes, **({"target": target} if target else {})})
        blob.extend(a.tobytes())
        d = {"bufferView": len(views) - 1, "componentType": ct, "count": len(a), "type": typ}
        if minmax:
            d["min"], d["max"] = a.min(0).tolist(), a.max(0).tolist()
        acc.append(d)
        return len(acc) - 1

    def mat(name):
        if name not in [m["name"] for m in mats]:
            mats.append(dict((materials or {}).get(name) or {"name": name, "doubleSided": True}))
        return [m["name"] for m in mats].index(name)

    for n in nodes:
        att = {"POSITION": put(np.asarray(n["P"], np.float32), "VEC3", 5126, 34962, True),
               "NORMAL": put(np.asarray(n["N"], np.float32), "VEC3", 5126, 34962)}
        for key, k, typ in (("uv0", "TEXCOORD_0", "VEC2"), ("uv1", "TEXCOORD_1", "VEC2"), ("col", "COLOR_0", "VEC4")):
            if n.get(key) is not None:
                att[k] = put(np.asarray(n[key], np.float32), typ, 5126, 34962)
        pr = {"attributes": att, "indices": put(np.asarray(n["T"], np.uint32).reshape(-1), "SCALAR", 5125, 34963),
              "material": mat(n["material"])}
        m = {"name": n["name"], "primitives": [pr]}
        if n.get("extras"):
            m["extras"] = n["extras"]
        meshes.append(m)
        out_nodes.append({"name": n["name"], "mesh": len(meshes) - 1})
    js = {"asset": {"version": "2.0", "generator": "Survivor Unchained tools/armor/gear_native.py", "extras": extras or {}},
          "scene": 0, "scenes": [{"nodes": list(range(len(out_nodes)))}], "nodes": out_nodes, "meshes": meshes,
          "materials": mats, "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": len(blob)}], **(tail or {})}
    while len(blob) % 4:
        blob.append(0)
    js["buffers"][0]["byteLength"] = len(blob)
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(jb) + len(blob)))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A) + jb)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))


def read_parts(glb):
    """[{name, material, P, N, T, uv0, uv1, col, transform}] of a piece glb's mesh nodes."""
    sys.path.insert(0, os.path.join(REPO, "tools", "anim"))
    from skin import Gltf
    g = Gltf(glb)
    js, out = g.js, []
    for n in js["nodes"]:
        if "mesh" not in n:
            continue
        prims = js["meshes"][n["mesh"]]["primitives"]
        pr = prims[0]
        a = pr["attributes"]
        get = lambda k: g.accessor(a[k]).astype(np.float32) if k in a else None  # noqa: E731
        mi = pr.get("material")
        out.append({"name": n.get("name", ""), "prims": len(prims), "P": get("POSITION"), "N": get("NORMAL"),
                    "T": g.accessor(pr["indices"]).reshape(-1, 3).astype(np.int64) if "indices" in pr else None,
                    "uv0": get("TEXCOORD_0"),
                    "uv1": get("TEXCOORD_1"), "col": get("COLOR_0"),
                    "material": js["materials"][mi].get("name", "") if mi is not None else "",
                    "transform": any(k in n for k in ("translation", "rotation", "scale", "matrix"))})
    return out


# ---------------------------------------------------------------- the contract

def load_piece(d):
    pj = os.path.join(d, "piece.json")
    piece = json.load(open(pj, encoding="utf-8"))
    return piece, os.path.join(d, f"{piece.get('id', os.path.basename(os.path.normpath(d)))}.glb")


def part_rule(piece, name, seen=()):
    """A rigid part's ride rule, its own or the part's it is fixed to (None when it has none)."""
    r = (piece.get("parts") or {}).get(name)
    if not r or name in seen:
        return None
    if "ride" in r or "bones" in r:
        return r
    return part_rule(piece, r.get("with", ""), seen + (name,)) if r.get("with", "").endswith("_rigid") else None


def lead_part(piece, name):
    r = (piece.get("parts") or {}).get(name) or {}
    own = "ride" in r or "bones" in r
    return lead_part(piece, r["with"]) if not own and r.get("with") in (piece.get("parts") or {}) else name


def bones_blend(names, D, bones):
    """A rigid part's blend named bone by bone: {bone: share} ("{s}" = the side its skin leans to, by the mean weights
    D over its bound points) -> dense weights over `names`, normalised. A bone this body has not is refused."""
    side = np.array([n[-2:] for n in names])
    lean = "l" if D[side == "_l"].sum() >= D[side == "_r"].sum() else "r"
    out = np.zeros(len(names))
    for b, v in bones.items():
        n = b.replace("{s}", lean)
        if n not in names:
            raise SystemExit(f"gear_native: a part's \"bones\" names '{n}', a bone this body has not")
        out[list(names).index(n)] += float(v)
    if out.sum() <= 0:
        raise SystemExit("gear_native: a part's \"bones\" shares sum to nothing")
    return out / out.sum()


CARRY = ("none", "part")
CARRY_SHAPES = ("arm_hang_", "elbow_")   # her corrective shapes a part with "carry": "part" follows
BEND = {"max": 1.0, "smooth": 0.02, "clear": 0.0024, "clips": "all"}   # a "bend" rule's keys and defaults
BEND_EPS = 1e-4         # (m) bending must raise a point this much over a frame before that frame asks it to bend
BEND_REPORT = {}        # {unit id: {part: stats}}: the last build's solve, per bent part


def bend_kernel(X, r):
    """(K, pairs): the row-normalised biweight kernel of radius r over the points X (sparse [n, n], self weight 1) and
    the point pairs within r (what the max filter reads)."""
    import scipy.sparse as sp
    from scipy.spatial import cKDTree
    n = len(X)
    pr = cKDTree(X).query_pairs(r, output_type="ndarray") if n > 1 else np.zeros((0, 2), int)
    w = (1.0 - (np.linalg.norm(X[pr[:, 0]] - X[pr[:, 1]], axis=1) / r) ** 2) ** 2
    K = sp.csr_matrix((np.r_[w, w, np.ones(n)], (np.r_[pr[:, 0], pr[:, 1], np.arange(n)], np.r_[pr[:, 1], pr[:, 0], np.arange(n)])), (n, n))
    return sp.diags(1.0 / np.asarray(K.sum(1)).ravel()) @ K, pr


def max_filter(x, pr):
    m = x.copy()
    np.maximum.at(m, pr[:, 0], x[pr[:, 1]])
    np.maximum.at(m, pr[:, 1], x[pr[:, 0]])
    return m


def bend_blend(Ds, j, w, K):
    """(B, Wr, Wt): a bent part's FIXED bone set (its ride's bones, then the others her smoothed skin weights K @ Ds lean
    on most, to 8) and its two blends over it per point: the ride (rigid) and her smoothed skin projected on B. Any
    alpha's blend (1-a) Wr + a Wt stays on B: no influence ever switches, and alpha 0 is the ride exactly."""
    KD = np.asarray(K @ Ds)
    ride = [int(b) for b, v in zip(j, w) if v > 0]
    others = [int(b) for b in np.argsort(-KD.sum(0)) if int(b) not in ride and KD[:, b].sum() > 0][:max(0, 8 - len(ride))]
    B = np.array(ride + others, int)
    Wr = np.zeros((len(Ds), len(B)))
    for b, v in zip(j, w):
        if v > 0:
            Wr[:, ride.index(int(b))] += v
    Wr /= Wr.sum(1, keepdims=True)
    Wt = KD[:, B]
    s = Wt.sum(1, keepdims=True)
    Wt = np.where(s > 1e-9, Wt / np.maximum(s, 1e-12), Wr)
    return B, Wr, Wt


def bend_heights(body, S, index, groups, alphas, chunk=96, reach=0.07):
    """Per group (need [n], low [n]): over each group's clips' frames, the alpha each point needs to stand its clear
    height over her moving skin (linear blend, no corrective shapes: native_travel.skin) and its lowest height at its
    current alphas. LBS is linear in the weights, so a point's pose at alpha a is (1-a) P_ride + a P_skin exactly; a
    point's need over a frame is a + (L - h_a) / (h_skin - h_ride) where it is under L and bending lifts it. L = the
    rule's "clear", or the point's own height at rest when that is less (no point is asked to stand higher than it is
    built)."""
    import native_travel as nt
    from scipy.spatial import cKDTree
    Xall = np.vstack([gr["X"] for gr in groups])
    vs = np.unique(np.concatenate(cKDTree(body.V).query_ball_point(Xall, reach)).astype(int))
    tree0 = cKDTree(body.V[vs])
    jm = np.array([index[n] for n in body.joint_names])
    out = []
    for gr in groups:
        jn = tree0.query(gr["X"])[1]
        h0 = ((gr["X"] - body.V[vs][jn]) * body.N[vs][jn]).sum(1)
        out.append({"L": np.minimum(gr["spec"]["clear"], h0), "need": np.zeros(len(gr["X"])), "low": np.full(len(gr["X"]), np.inf)})
    for c0 in range(0, len(S), chunk):
        Sf = S[c0:c0 + chunk]
        V, N = nt.skin(body, Sf, index, vs)
        P = []
        for gr, a in zip(groups, alphas):
            Sb = Sf[:, jm[gr["B"]]]
            pos = np.einsum("fkij,nj->fnki", Sb[:, :, :3, :3], gr["X"]) + Sb[:, None, :, :3, 3]
            Pr, Pt = np.einsum("fnki,nk->fni", pos, gr["Wr"]), np.einsum("fnki,nk->fni", pos, gr["Wt"])
            P.append((Pr, Pt, (1 - a)[None, :, None] * Pr + a[None, :, None] * Pt))
        for fi in range(len(Sf)):
            t = cKDTree(V[fi])
            for gr, a, o, (Pr, Pt, Pa) in zip(groups, alphas, out, P):
                if not gr["frames"][c0 + fi]:
                    continue
                h = []
                for Q in (Pr[fi], Pt[fi], Pa[fi]):
                    k = t.query(Q)[1]
                    h.append(((Q - V[fi][k]) * N[fi][k]).sum(1))
                hr, ht, ha = h
                worse = ha < o["low"]
                o.setdefault("at", np.zeros(len(ha), int))[worse] = c0 + fi
                o["low"] = np.minimum(o["low"], ha)
                o["short"] = np.maximum(o.get("short", 0.0), o["L"] - ha)
                lift = ht - hr
                ask = (ha < o["L"]) & (lift > BEND_EPS)
                o["need"][ask] = np.maximum(o["need"][ask], a[ask] + (o["L"][ask] - ha[ask]) / lift[ask])
    return out


def bend_solve(body, groups, S=None, index=None, passes=3):
    """The alpha field per group ([n] in [0, max]): a bent part's points move (1-a) with its ride and a with her
    skin's own weights (smoothed), and a is only as large as her moving skin asks: alpha = K @ maxfilter(need) (>= the
    need by construction, smooth at the kernel's radius); each pass re-measures the need at the new field and keeps
    the larger (so alpha never drops and never creeps past the need's own reach). Returns (alphas, stats) where stats per group has the passes' lowest heights."""
    if S is None:
        import native_travel as nt
        z = nt.frames()
        S, index = z["S"], z["index"]
        for gr in groups:
            gr.setdefault("frames", nt.clip_frames(gr["spec"]["clips"]))
    for gr in groups:
        gr.setdefault("frames", np.ones(len(S), bool))
    alphas = [np.zeros(len(gr["X"])) for gr in groups]
    needs = [np.zeros(len(gr["X"])) for gr in groups]
    lows = [[] for _ in groups]
    for _ in range(passes):
        res = bend_heights(body, S, index, groups, alphas)
        for k, (gr, o) in enumerate(zip(groups, res)):
            lows[k].append(float(o["low"].min()))
            needs[k] = np.maximum(needs[k], o["need"])     # (the need is kept, never the smoothed field: no creep)
            alphas[k] = np.clip(np.asarray(gr["K"] @ max_filter(needs[k], gr["pairs"])).ravel(), 0.0, gr["spec"]["max"])
    res = bend_heights(body, S, index, groups, alphas)
    for k, o in enumerate(res):
        lows[k].append(float(o["low"].min()))
    return alphas, [{"low_by_pass_mm": [round(v * 1000, 2) for v in lw], "low": res[k]["low"],
                     "short": np.maximum(res[k].get("short", np.zeros(len(alphas[k]))), 0.0),
                     "at": res[k].get("at", np.zeros(len(alphas[k]), int))} for k, lw in enumerate(lows)]


def rigid_fit(X, Y):
    """The rigid motion (R, t) with X @ R.T + t ~ Y (least squares, no mirror)."""
    cx, cy = X.mean(0), Y.mean(0)
    u, _, vt = np.linalg.svd((X - cx).T @ (Y - cy))
    R = vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(vt.T @ u.T))]) @ u.T
    return R, cy - R @ cx


def open_scalp(parts, head_P, head_N, mask):
    """How many of the scalp mask's head points no helm face covers (within SCALP_COVER_M, outward of the point)."""
    sys.path.insert(0, os.path.join(REPO, "tools", "body"))
    from surfdist import Surface
    P = np.vstack([p["P"] for p in parts]).astype(np.float64)
    T = np.vstack([p["T"] + o for p, o in zip(parts, np.cumsum([0] + [len(p["P"]) for p in parts[:-1]]))])
    x, n = head_P[mask], head_N[mask]
    q = Surface(P, T).closest(x, k=min(24, len(T)))[0]
    d = q - x
    return int(((np.linalg.norm(d, axis=1) > SCALP_COVER_M) | ((d * n).sum(1) < -1e-4)).sum())


def validate(d, rest_hash=None, head=None, mask=None, materials=None):
    """Why this piece dir cannot be bound: a list of plain reasons, empty when it can. rest_hash: the bind body's
    {tier: sha1} (read from body_p1 when None); head (P, N) and mask: her head and its scalp mask (read when None and
    the piece hides her hair)."""
    why = []
    pj = os.path.join(d, "piece.json")
    if not os.path.exists(pj):
        return [f"no piece.json in {d}"]
    try:
        piece, glb = load_piece(d)
    except ValueError as e:
        return [f"piece.json is not JSON ({e})"]
    pid = piece.get("id", "")
    if not re.fullmatch(r"[a-z0-9_]+", pid) or pid != os.path.basename(os.path.normpath(d)):
        why.append(f"id '{pid}' must be [a-z0-9_]+ and the folder's name")
    if piece.get("slot") not in SLOTS:
        why.append(f"unknown slot '{piece.get('slot')}' (one of {', '.join(SLOTS)})")
    stamp = (piece.get("native") or {}).get("rest_hash")
    if not stamp:
        why.append("missing rest stamp: piece.json native.rest_hash names the body it was modelled on")
    else:
        if rest_hash is None:
            g = gf()
            rest_hash = {t: g.sha1(os.path.join(g.BIND_BODY, "body.glb" if t == "close" else "play.glb")) for t in g.TIERS}
        if stamp.get("close") != rest_hash.get("close"):
            why.append(f"modelled on another body (rest stamp {str(stamp.get('close'))[:8]}, her_b is "
                       f"{str(rest_hash.get('close'))[:8]}): rebuild it on the current body")
    if not os.path.exists(glb):
        return why + [f"no mesh {os.path.basename(glb)}"]
    parts = read_parts(glb)
    if not parts:
        return why + ["the mesh file has no mesh nodes"]
    known = materials if materials is not None else set(json.load(open(MATERIALS, encoding="utf-8")))
    for p in parts:
        if p["transform"]:
            why.append(f"part '{p['name']}' has a node transform (apply transforms: the mesh stands at her rest)")
        if p["prims"] != 1:
            why.append(f"part '{p['name']}' has {p['prims']} primitives (one material a part)")
        if p["material"] not in known:
            why.append(f"part '{p['name']}': unknown material '{p['material']}' (a name from outfit_materials.json)")
        if p["N"] is None:
            why.append(f"part '{p['name']}' has no normals")
        if p["T"] is None:
            why.append(f"part '{p['name']}' has no indices (export an indexed triangle list)")
        if p["name"].endswith("_rigid") and part_rule(piece, p["name"]) is None:
            why.append(f"rigid part '{p['name']}' has no role: piece.json parts needs its \"ride\" or the part it is fixed \"with\"")
    for name, r in (piece.get("parts") or {}).items():
        if r.get("carry", "none") not in CARRY or ("carry" in r and "bones" not in r):
            why.append(f"part '{name}': \"carry\" is one of {', '.join(CARRY)}, on a part that names its \"bones\"")
        if "bend" in r and ("bones" not in r or not isinstance(r["bend"], dict) or set(r["bend"]) - set(BEND)):
            why.append(f"part '{name}': \"bend\" is {{{', '.join(BEND)}}}, on a part that names its \"bones\"")
    if any(p["T"] is None for p in parts):
        return why
    P = np.vstack([p["P"] for p in parts])
    if P[:, 1].min() < -0.05 or P[:, 1].max() > 2.0 or np.abs(P[:, [0, 2]]).max() > 0.6:
        why.append(f"bounds {P.min(0).round(2).tolist()}..{P.max(0).round(2).tolist()} miss her body (metres, Y up, feet on y = 0)")
    if piece.get("hair") == "hide":
        if piece.get("slot") != "head":
            why.append("only a head piece may hide her hair")
        elif stamp and not why:
            if mask is None:
                if not os.path.exists(SCALP):
                    return why + [f"no scalp mask ({rel(SCALP)}): a hair-hiding helm is checked against it"]
                mask = np.array(json.load(open(SCALP))["head_verts"], np.int64)
            if head is None:
                b = gf().Body.load(gf().BIND_BODY, "close")
                head = (b.V[b.nt:], b.N[b.nt:])
            n_open = open_scalp(parts, head[0], head[1], mask)
            if n_open:
                why.append(f"open scalp: {n_open} of {len(mask)} scalp points are not under the helm, and it hides her hair")
    return why


# ---------------------------------------------------------------- units, bind

def native_units():
    out = []
    for name in sorted(os.listdir(NATIVE)) if os.path.isdir(NATIVE) else []:
        d = os.path.join(NATIVE, name)
        if not os.path.exists(os.path.join(d, "piece.json")):
            continue
        piece, glb = load_piece(d)
        mats = sorted({p["material"] for p in read_parts(glb)}) if os.path.exists(glb) else []
        slot = piece["slot"]
        row = {"id": piece["id"], "outfit": None, "slot": slot, "layer": piece.get("layer", LAYER.get(slot, 1)),
               "covers": piece.get("covers", [slot]), "meshes": [f"{piece['id']}.{slot}.{m}" for m in mats],
               "tier": piece.get("tier", 1), "native": True}
        for k in ("hair", "style", "name", "cover_grow", "replaces"):
            if k in piece:
                row[k] = piece[k]
        sk = os.path.join(d, f"{piece['id']}.sockets.json")
        out.append({"id": piece["id"], "kind": "native", "row": row, "src": rel(glb), "dir": d, "rigid_row": True,
                    "meshes": [(m, "close", True) for m in row["meshes"]], "sockets": rel(sk) if os.path.exists(sk) else None})
    return out


def material_templates():
    """A shared material's glTF definition with its textures, from the first gear source that has it."""
    g = gf()
    for base, pre in ((g.ARMOR, ("plate_", "mar_")), (g.PEOPLE, ("heroine_outfit_",))):
        for f in sorted(os.listdir(base)):
            if f.endswith(".gltf") and f.startswith(pre):
                yield os.path.join(base, f), json.load(open(os.path.join(base, f)))


def merge_parts(piece, parts):
    """The parts merged per material: [{name '<id>.<slot>.<material>', P, N, T, uv0, uv1, col, material, extras, part
    (per vertex: the part's index), names}] in material order."""
    pid, slot = piece["id"], piece["slot"]
    out = []
    for mat in sorted({p["material"] for p in parts}):
        ps = [(k, p) for k, p in enumerate(parts) if p["material"] == mat]
        off = np.cumsum([0] + [len(p["P"]) for _, p in ps])
        fill = lambda p, key, w, v: p[key] if p[key] is not None else np.full((len(p["P"]), w), v, np.float32)  # noqa: E731
        out.append({"name": f"{pid}.{slot}.{mat}", "material": mat,
                    "P": np.vstack([p["P"] for _, p in ps]), "N": np.vstack([p["N"] for _, p in ps]),
                    "T": np.vstack([p["T"] + o for (_, p), o in zip(ps, off)]),
                    "uv0": np.vstack([fill(p, "uv0", 2, 0) for _, p in ps]), "uv1": np.vstack([fill(p, "uv1", 2, 0.05) for _, p in ps]),
                    "col": np.vstack([fill(p, "col", 4, 1) for _, p in ps]),
                    "part": np.concatenate([np.full(len(p["P"]), k) for k, p in ps]),
                    "extras": {"outfit": pid, "slot": slot, "material": mat, "rank": 0, "tier": piece.get("tier", 1),
                               "pieces": [[i, int(len(p["T"]))] for i, (_, p) in enumerate(ps)]}})
    return out


def write_src(path, piece, merged):
    """<id>.src.glb beside the binding: the merged meshes with the shared materials' own textures (uris from here)."""
    # (a key whose outfit_materials.json row names a "template" takes that key's glTF material and textures under its
    # own name: plainsteel is steel's scan, drawn bare by the game because it has no finish in metal_finishes.json.
    # Without one a key no gear source carries came out as a bare white material. The rule is gear_finish's, shared
    # with a record's "finish" in the fit build.)
    import gear_finish
    mats, tail = gear_finish.template_materials({m["material"] for m in merged}, os.path.dirname(path),
                                                json.load(open(MATERIALS, encoding="utf-8")), material_templates())
    write_glb(path, merged, {"gear_native": {"piece": piece["id"]}}, mats, tail)


def bind_native(u, bodies):
    """One native unit: validated, merged per material, each vertex bound where it stands (the identity on her_b)."""
    g = gf()
    t0 = time.time()
    d = u.get("dir") or os.path.dirname(os.path.join(REPO, u["src"]))
    body = bodies["close"]
    why = validate(d, rest_hash={t: bodies[t].hash for t in g.TIERS}, head=(body.V[body.nt:], body.N[body.nt:]))
    if why:
        raise SystemExit(f"gear_native: {u['id']} refused:\n  " + "\n  ".join(why))
    piece, glb = load_piece(d)
    parts = read_parts(glb)
    merged = merge_parts(piece, parts)
    os.makedirs(g.BIND, exist_ok=True)
    src = os.path.join(g.BIND, f"{u['id']}.src.glb")
    write_src(src, piece, merged)
    names = [p["name"] for p in parts]
    rigid = [n.endswith("_rigid") for n in names]
    lead = np.array([names.index(lead_part(piece, n)) if r else k for k, (n, r) in enumerate(zip(names, rigid))], np.int32)
    arrays, metas, rep = {"lead_close": lead}, [], {"id": u["id"], "src": u["src"], "meshes": {}}
    for i, m in enumerate(merged):
        # (unique positions within a part: two parts never share a binding, so a rivet never welds to a strap)
        key = np.c_[m["P"].astype(np.float32), m["part"].astype(np.float32)]
        _, first, inv = np.unique(np.ascontiguousarray(key).view(np.dtype((np.void, 16))).reshape(-1), return_index=True, return_inverse=True)
        inv = inv.reshape(-1).astype(np.int32)
        X = m["P"][first].astype(np.float64)
        comp = np.where(np.array(rigid)[m["part"][first]], m["part"][first], -1).astype(np.int32)
        tri, bq, off, _ = g.bind_points(body, X)
        _, F = g.frames(body, tri.astype(np.int64), g.unq(bq))
        nloc = np.einsum("nji,nj->ni", F[inv], g.U(m["N"].astype(np.float64)))
        arrays.update({f"inv{i}": inv, f"tri{i}": tri, f"bw{i}": bq, f"off{i}": off, f"nrm{i}": g.snorm16(nloc), f"comp{i}": comp})
        metas.append({"i": i, "node": m["name"], "tier": "close", "rigid": bool((comp >= 0).any()), "nv": int(len(m["P"])), "nu": int(len(X))})
        Xe, _ = g.eval_points(body, tri, bq, off)
        c, _ = g.gear_field.signed_clear(body, X, k=16)
        rep["meshes"][m["name"]] = {"tier": "close", "verts": int(len(m["P"])), "uniques": int(len(X)), "tris": int(len(m["T"])),
                                    "rigid_points": int((comp >= 0).sum()), "identity_mm": round(float(np.abs(Xe - X).max() * 1000), 5),
                                    "inside": int((c < 0).sum()), "clear_mm_min_p50_max": [round(float(v) * 1000, 2) for v in (c.min(), np.median(c), c.max())]}
        os.makedirs(os.path.join(g.OUT, "_bindref"), exist_ok=True)
        np.save(os.path.join(g.OUT, "_bindref", f"{u['id']}.{i}.npy"), X)
    aux = g.socket_points(json.load(open(os.path.join(REPO, u["sockets"])))) if u.get("sockets") else None
    if aux:
        from scipy.spatial import cKDTree
        Pr = np.vstack([p["P"] for p, r in zip(parts, rigid) if r] or [np.zeros((0, 3))])
        Cr = np.concatenate([np.full(len(p["P"]), lead[k]) for k, (p, r) in enumerate(zip(parts, rigid)) if r] or [np.zeros(0, int)])
        comp = np.full(len(aux["P"]), -1)
        if len(Pr):
            dd, j = cKDTree(Pr).query(aux["P"])
            comp = np.where(dd < 0.05, Cr[j], -1)
        tri, bq, off, nl = g.bind_points(body, aux["P"], aux["N"])
        _, F = g.frames(body, tri.astype(np.int64), g.unq(bq))
        arrays.update({"aux_tri": tri, "aux_bw": bq, "aux_off": off, "aux_nrm": g.snorm16(nl),
                       "aux_up": g.snorm16(np.einsum("nji,nj->ni", F, aux["Up"])), "aux_comp": comp.astype(np.int32)})
    rules = [{"part": n, "comp": k, "rule": part_rule(piece, n)} for k, (n, r) in enumerate(zip(names, rigid)) if r and lead[k] == k]
    meta = {"id": u["id"], "kind": "native", "bind_version": g.BIND_VERSION, "src": rel(src), "src_sha1": g.sha1(glb),
            "piece_sha1": g.sha1(os.path.join(d, "piece.json")), "native_dir": rel(d), "bind_body": rel(g.BIND_BODY),
            "bind_hash": {t: bodies[t].hash for t in g.TIERS}, "meshes": metas, "sockets": u.get("sockets"),
            "aux": aux and {"keys": aux["keys"]}, "row": u["row"], "rigid_row": True, "parts": rules}
    arrays["meta"] = np.frombuffer(json.dumps(meta).encode(), np.uint8)
    np.savez_compressed(os.path.join(g.BIND, f"{u['id']}.npz"), **arrays)
    rep["secs"] = round(time.time() - t0, 1)
    return rep


def part_blends(bd, bodies, ev):
    """Each rigid part's own ride rule (piece.json parts) in place of its slot's: its one blend of weights. A part that
    names its bones ("bones") rides that blend EXACTLY: it takes none of her corrective shapes. The build gives every
    rigid component the mean of her shapes' deltas over its bound points; those answer her skin's own weights, and on
    a blend named bone by bone they move the part off it (the cuisses' knee lame, thigh_twist_02 0.8 + calf_share 0.2,
    went 13.8 mm into her knee and 10 mm round it at knee_flex135: her skin came through it in every run, and it
    dipped into the lame above). "carry": "part" on such a part: it follows her CARRY_SHAPES after all, each as ONE
    rigid motion (the rigid fit of her skin's delta over the part's footprint, the body points its own bound points
    stand on), applied to every point that rides it, its rims and rivets too: a shoulder lame that carries none sees
    her skin rise 16-24 mm under it in the attacks, and one whose trim carries its own mean leaves its plate."""
    g = gf()
    body, z = bodies["close"], bd.z
    lead = z["lead_close"]
    ms = [m for m in bd.meta["meshes"] if m["tier"] == "close"]
    comp = np.concatenate([z[f"comp{m['i']}"] for m in ms])
    trs = np.concatenate([z[f"tri{m['i']}"] for m in ms]).astype(np.int64)
    ws = np.vstack([g.unq(z[f"bw{m['i']}"]) for m in ms])
    rr = g.rigid_roles()
    off = np.cumsum([0] + [len(z[f"comp{m['i']}"]) for m in ms])
    bent = []
    for p in bd.meta.get("parts", []):
        if not p["rule"] or not (comp == p["comp"]).any():
            continue
        own = comp == p["comp"]
        if "bones" in p["rule"]:
            names = body.joint_names
            jj, ww = g.top_k(bones_blend(names, g.dense_weights(body, trs[own], ws[own], len(names)).mean(0), p["rule"]["bones"])[None])
            j, w = jj[0], ww[0]
            fits = {}
            if p["rule"].get("carry") == "part":
                vs = np.unique(body.T[trs[own]])
                for nm, dP in body.shapes.items():
                    if nm.startswith(CARRY_SHAPES) and np.abs(dP[vs]).max() > 1e-5:
                        fits[nm] = rigid_fit(body.V[vs], body.V[vs] + dP[vs])
        else:
            j, w = g.rigid_blend(body, trs[own], ws[own], "_", roles={"roles": rr.get("roles", {}), "anchors": rr.get("anchors", {}),
                                                                     "slots": {"_": p["rule"]}})
        if "bones" in p["rule"] and p["rule"].get("bend"):
            bent.append((p, j, w, fits))
        for m in ms:
            e = ev[m["node"]]
            ci = z[f"comp{m['i']}"]
            sel = ((ci >= 0) & (lead[np.maximum(ci, 0)] == p["comp"]))[e["inv"]]
            e["J"][sel], e["W"][sel] = j, w
            if "bones" in p["rule"]:
                for nm in e["shapes"]:
                    e["shapes"][nm][sel] = 0.0
                if sel.any():
                    X = e["Xu"][e["inv"]][sel] if fits else None
                    for nm, (R, t) in fits.items():
                        if nm not in e["shapes"]:
                            e["shapes"][nm] = np.zeros((len(sel), 3))
                        e["shapes"][nm][sel] = X @ R.T + t - X
    if bent:
        bend_parts(bd, body, ev, ms, comp, lead, trs, ws, off, bent)


def bend_parts(bd, body, ev, ms, comp, lead, trs, ws, off, bent, S=None, index=None):
    """The bent parts (a "bend" rule on a part that names its bones): each part group (the plate, its rims and rivets:
    one alpha field) gets weights (1-a) ride + a (her smoothed skin weights on its fixed bones) and, for her
    CARRY_SHAPES, (1-a) its rigid carry + a (her smoothed skin's own delta). Alpha 0 leaves the ride exactly. Nothing
    is written per vertex but the weights and shapes the game already reads."""
    g = gf()
    t0 = time.time()
    nj = len(body.joint_names)
    Xall = np.vstack([ev[m["node"]]["Xu"] for m in ms])
    groups = []
    for p, j, w, fits in bent:
        spec = {**BEND, **p["rule"]["bend"]}
        gsel = np.flatnonzero((comp >= 0) & (lead[np.maximum(comp, 0)] == p["comp"]))
        X = Xall[gsel]
        K, pairs = bend_kernel(X, float(spec["smooth"]))
        Ds = g.dense_weights(body, trs[gsel], ws[gsel], nj)
        B, Wr, Wt = bend_blend(Ds, j, w, K)
        groups.append({"part": p["part"], "spec": spec, "gsel": gsel, "X": X, "K": K, "pairs": pairs, "B": B, "Wr": Wr,
                       "Wt": Wt, "j": j, "w": w, "fits": fits})
    alphas, stats = bend_solve(body, groups, S, index)
    rep = BEND_REPORT.setdefault(bd.meta.get("id", "?"), {})
    for gr, a, st in zip(groups, alphas, stats):
        au = np.zeros(len(Xall))
        au[gr["gsel"]] = a
        rows = np.full(len(Xall), -1)
        rows[gr["gsel"]] = np.arange(len(gr["gsel"]))
        Tg = body.T[trs[gr["gsel"]]]
        for i, m in enumerate(ms):
            e = ev[m["node"]]
            r = rows[off[i]:off[i + 1]][e["inv"]]
            sel = np.flatnonzero((r >= 0) & (au[off[i]:off[i + 1]][e["inv"]] > 0))
            if not len(sel):
                continue
            rs, av = r[sel], a[r[sel]]
            D = np.zeros((len(sel), nj))
            D[:, gr["B"]] = (1 - av)[:, None] * gr["Wr"][rs] + av[:, None] * gr["Wt"][rs]
            e["J"][sel], e["W"][sel] = g.top_k(D)
            X = e["Xu"][e["inv"]][sel]
            for nm, dP in body.shapes.items():
                if not nm.startswith(CARRY_SHAPES):
                    continue
                sk = np.asarray(gr["K"] @ (ws[gr["gsel"]][:, :, None] * dP[Tg]).sum(1))[rs]
                rig = X @ gr["fits"][nm][0].T + gr["fits"][nm][1] - X if nm in gr["fits"] else 0.0
                d = (1 - av)[:, None] * rig + av[:, None] * sk
                if nm not in e["shapes"]:
                    if np.abs(d).max() <= 1e-5:
                        continue
                    e["shapes"][nm] = np.zeros((len(e["inv"]), 3))
                e["shapes"][nm][sel] = d
        rep[gr["part"]] = st = {"alpha_p50_p95_max": [round(float(v), 3) for v in (np.median(a), np.percentile(a, 95), a.max())],
                                "bent_share": round(float((a > 1e-6).mean()), 3), "points": int(len(a)),
                                "low_by_pass_mm": st["low_by_pass_mm"], "min_clear_mm": round(float(st["low"].min()) * 1000, 2),
                                "short_max_mm": round(float(st["short"].max()) * 1000, 2), "bones": [body.joint_names[b] for b in gr["B"]]}
        if S is None:       # (where it is lowest: the clips of the points more than 1 mm under their clear height)
            import native_travel as nt
            fz = nt.frames()
            k = np.flatnonzero(stats[groups.index(gr)]["short"] > 0.001)
            cl, cn = np.unique(fz["clip"][stats[groups.index(gr)]["at"][k]], return_counts=True)
            st["short_clips"] = dict(sorted(zip(cl.tolist(), cn.tolist()), key=lambda t: -t[1])[:6])
            print(f"    {gr['part']} short by clip: {st['short_clips']}; worst at {X[:0].shape and ''}"
                  f"{fz['clip'][stats[groups.index(gr)]['at'][np.argmax(stats[groups.index(gr)]['short'])]]}")
        print(f"  bend {bd.meta.get('id', '?')}/{gr['part']}: alpha p50/p95/max {st['alpha_p50_p95_max']}, bent {st['bent_share']:.1%}"
              f" of {st['points']}, min clear {st['min_clear_mm']} mm (by pass {st['low_by_pass_mm']}), worst short {st['short_max_mm']} mm")
    print(f"  bend solve {bd.meta.get('id', '?')}: {len(groups)} parts, {time.time() - t0:.1f} s")


def install(g):
    """gear_fit's one hook: the native dirs join its units, bind, stale and build."""
    global _GF
    _GF = g
    if getattr(g, "_native", False):
        return
    units0, bind0, stale0, eval0 = g.units, g.bind_unit, g.stale_units, g.eval_unit

    def units():
        return units0() + native_units()

    def bind_unit(u, car, bodies):
        return bind_native(u, bodies) if u.get("kind") == "native" else bind0(u, car, bodies)

    def stale_units(bodies=None, bind_dir=None, unit_list=None):
        unit_list = g.units() if unit_list is None else unit_list
        out, orphans = stale0(bodies, bind_dir, unit_list)
        bad = {uid for uid, _ in out}
        for u in unit_list:
            if u.get("kind") == "native" and u["id"] not in bad:
                meta = json.loads(bytes(np.load(os.path.join(bind_dir or g.BIND, f"{u['id']}.npz"))["meta"]).decode())
                if meta.get("piece_sha1") != g.sha1(os.path.join(u["dir"], "piece.json")):
                    out.append((u["id"], "piece.json changed"))
        return out, orphans

    def eval_unit(bd, bodies, bind_bodies, stats=None):
        ev = eval0(bd, bodies, bind_bodies, stats)
        if bd.meta.get("kind") == "native":
            part_blends(bd, bodies, ev)
        return ev

    g.units, g.bind_unit, g.stale_units, g.eval_unit, g._native = units, bind_unit, stale_units, eval_unit, True


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("validate", "bind", "list"))
    ap.add_argument("dir", nargs="?")
    a = ap.parse_args()
    g = gf()
    if a.cmd == "list":
        for u in native_units():
            print(u["id"], u["row"]["slot"], u["src"])
        return
    d = os.path.abspath(a.dir)
    if a.cmd == "validate":
        why = validate(d)
        print("\n".join(f"REFUSED: {w}" for w in why) or f"gear_native: {rel(d)} is a valid native piece")
        sys.exit(1 if why else 0)
    u = next((u for u in native_units() if os.path.samefile(u["dir"], d)), None)
    if u is None:
        raise SystemExit(f"gear_native: {d} is not a piece dir under {rel(NATIVE)}")
    bodies = {t: g.Body.load(g.BIND_BODY, t) for t in g.TIERS}
    r = bind_native(u, bodies)
    print(u["id"], r["secs"], "s")
    for k, v in r["meshes"].items():
        print("   ", k, v)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    import gear_native as me   # (one copy of this module: gear_fit's hook imports it by name)
    me.main()
