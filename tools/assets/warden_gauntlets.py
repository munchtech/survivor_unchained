"""The Ford-Warden's articulated gauntlet fingers (Warden 7: "gauntlets: five separate finger plates per hand").

    python tools/assets/warden_gauntlets.py [--pkg godot/art/npc/ford_warden]

The Meshy body's gauntlets are mittens: the hand and its fingers one paddle, rigid on hand_l/hand_r, so his fists
never close. This builds the plates as a package piece on body.glb's skeleton: per finger three overlapping lames
(index, middle, ring, pinky: on _01, _02, _03; each one's proximal end flared over the end of the one before, the
last closed in a rounded tip), the thumb two (_02, _03), a knuckle plate across the four knuckles and a rolled cuff
edge at the wrist (both on the hand bone). Every lame is rigid on its own bone, laid in that bone's rest frame (the
fingers along +Y, the knuckle line along X, the palm toward +Z), so it follows the clips' and NpcHands' curls.

The right hand's index, middle and ring _01 bones are broken in the package's rest (their heads 13-17 cm off the
hand, outside the mitten; Idle_Shield swung index_02_r 17 cm from the hand). The plates are laid on the mirrored left
hand's _01 rests instead, and this piece's inverse binds for those bones are made from them; WardenGauntlets.cs sets
the same rests on his skeleton at run time (FixRightHand), so the clips' rotations turn those fingers about their real
knuckles.

The mitten's fingers past the knuckle line are listed for WardenGauntlets.Trim (a baked package has no piece hide):
armor/gauntlets_tuck.bin, the tuck-record format (int32 count, then int32 x, y, z in glTF metres x 1e5 and a float)
of body.glb's and lod.glb's "generated" vertices on the hands beyond the knuckles; a triangle goes when its three
corners are listed.

Out: armor/gauntlets.glb (meshes gauntlets.iron, gauntlets.lod1.iron, gauntlets.shadow; material
warden_gauntlet_iron, drawn by WardenLook on warden_wet.gdshader as the body's iron class by its own ID map),
armor/gauntlets_id.png (R = class 4 * 32 + convexity: the lames' rims and the back ridge worn, the class's own
look elsewhere), armor/gauntlets_tuck.bin, and the numbers on stdout.
"""
import io, json, math, os, struct, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_nobpy import Glb  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG = os.path.join(ROOT, "godot", "art", "npc", "ford_warden")
FINGERS = ("index", "middle", "ring", "pinky")
# the lames' half-widths (across the knuckle line), m; their thickness is TH of it
WIDTH = {"index": 0.0118, "middle": 0.0124, "ring": 0.0116, "pinky": 0.0100, "thumb": 0.0132}
TH = 0.80
FIXED = ("index", "middle", "ring")   # the right hand's broken _01 rests
CUT = 0.004                            # the mitten hidden from this far past the knuckle line (hand-local y)
NA = 12                                # points round a lame
UV_LAME = 0.72                         # lames' v in [0, UV_LAME]; the knuckle plate and cuff above


def log(*a):
    print("[gauntlets]", *a, flush=True)


def skeleton(g):
    j = g.j
    sk = j["skins"][0]
    names = [j["nodes"][n]["name"] for n in sk["joints"]]
    IBM = g.acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
    G = {n: np.linalg.inv(IBM[i]) for i, n in enumerate(names)}   # bind = rest (checked: 0 difference)
    return names, IBM, G


def fixed_rests(G):
    """The right hand's index/middle/ring _01 global rests: the left's, relative to its hand, mirrored in x."""
    S = np.diag([-1.0, 1, 1, 1])
    out = {}
    for f in FIXED:
        L = np.linalg.inv(G["hand_l"]) @ G[f"{f}_01_l"]
        out[f"{f}_01_r"] = G["hand_r"] @ (S @ L @ S)
    return out


def lame(L, rw, rh, y0, y1, flare, tip=False, rows=5, na=NA):
    """A closed elliptical shell along +Y in its bone's frame, from y0 to y1; the back (-Z) has a low medial ridge,
    its proximal end flared by `flare`; a tip closes it in a rounded cap. Returns V, F, UV (v along, u round), rim."""
    th = np.linspace(0, 2 * np.pi, na, endpoint=False)
    V, UV, rim = [], [], []
    ys = list(np.linspace(y0, y1, rows))
    sc = [1.0 + (flare - 1.0) * max(0.0, 1 - (y - y0) / (0.22 * (y1 - y0) + 1e-9)) for y in ys]
    sc[0] = flare * 1.02
    if tip:
        for k, a in enumerate((0.75, 0.42)):
            ys.append(y1 + rw * (0.45 if k == 0 else 0.78))
            sc.append(a)
    for r, (y, s) in enumerate(zip(ys, sc)):
        for t in th:
            x, z = rw * s * math.cos(t), rh * s * math.sin(t)
            if z < 0:
                z -= 0.0016 * s * math.exp(-(x / (0.38 * rw)) ** 2)      # the back's ridge
            else:
                z *= 0.82                                                # the palm side flatter, close on the finger
            V.append((x, y, z))
            UV.append((t / (2 * np.pi), UV_LAME * (y - y0) / ((ys[-1] if tip else y1) - y0 + 1e-9)))
            rim.append(1.0 if r in (0, rows - 1) and not (tip and r == rows - 1) else (0.75 if z < 0 and abs(x) < 0.3 * rw else 0.5))
    n = len(ys)
    F = []
    for r in range(n - 1):
        for k in range(na):
            a, b = r * na + k, r * na + (k + 1) % na
            F += [(a, b, b + na), (a, b + na, a + na)]
    # caps: the proximal end open into the knuckle plate / the lame before is closed with a fan, the tip with a point
    c0 = len(V); V.append((0, ys[0], 0)); UV.append((0.5, 0.0)); rim.append(0.5)
    for k in range(na):
        F.append((c0, (k + 1) % na, k))
    c1 = len(V); V.append((0, ys[-1] + (rw * 0.18 if tip else 0), 0)); UV.append((0.5, UV_LAME)); rim.append(0.6)
    for k in range(na):
        F.append((c1, (n - 1) * na + k, (n - 1) * na + (k + 1) % na))
    V = (L @ np.c_[np.array(V), np.ones(len(V))].T).T[:, :3]
    return V, np.array(F), np.array(UV), np.array(rim)


def tube(pts, half_a, half_b, ax_a, ax_b, closed=False, na=8, uv_v=(UV_LAME, 1.0), bumps=None):
    """A lofted tube through pts (N x 3) with an elliptical section (half_a along ax_a, half_b along ax_b, per point)."""
    V, UV, rim = [], [], []
    N = len(pts)
    for i, p in enumerate(pts):
        for k in range(na):
            t = 2 * np.pi * k / na
            hb = half_b[i] * (1.0 + (bumps[i] if bumps is not None else 0.0) * max(0.0, math.sin(t)))
            V.append(p + ax_a[i] * half_a[i] * math.cos(t) + ax_b[i] * hb * math.sin(t))
            UV.append((k / na, uv_v[0] + (uv_v[1] - uv_v[0]) * i / max(N - 1, 1)))
            rim.append(0.9 if abs(math.cos(t)) > 0.8 else 0.6)
    F = []
    for i in range(N - 1 + (1 if closed else 0)):
        i1 = (i + 1) % N
        for k in range(na):
            a, b = i * na + k, i * na + (k + 1) % na
            c, d = i1 * na + (k + 1) % na, i1 * na + k
            F += [(a, b, c), (a, c, d)]
    if not closed:
        for end, rng in ((0, range(na)), (N - 1, range(na))):
            c = len(V); V.append(pts[end]); UV.append((0.5, uv_v[0])); rim.append(0.6)
            for k in rng:
                a, b = end * na + k, end * na + (k + 1) % na
                F.append((c, b, a) if end == 0 else (c, a, b))
    return np.array(V), np.array(F), np.array(UV), np.array(rim)


def hand_parts(side, G, P_hand, lod=False):
    """Every part of one hand: (bone, V global bind, F, UV, rim)."""
    na = 6 if lod else NA
    rows = 3 if lod else 5
    parts = []
    H = G[f"hand_{side}"]
    for f in FINGERS + ("thumb",):
        rw = WIDTH[f]; rh = rw * TH
        ks = (2, 3) if f == "thumb" else (1, 2, 3)
        for n, k in enumerate(ks):
            b = f"{f}_0{k}_{side}"
            ch = f"{f}_0{k + 1}_{side}" if k < 3 else f"{f}_04_leaf_{side}"
            L = G[b]
            off = (np.linalg.inv(L) @ G[ch])[:3, 3]
            ln = float(np.linalg.norm(off))
            # the lame's own frame: +Y toward the child joint
            yv = off / ln
            xv = np.array([1.0, 0, 0]) - yv * yv[0]; xv /= np.linalg.norm(xv)
            zv = np.cross(xv, yv)
            A = np.eye(4); A[:3, 0], A[:3, 1], A[:3, 2] = xv, yv, zv
            taper = (1.0, 0.95, 0.90)[n if f != "thumb" else n + 1]
            first = n == 0
            y0 = -rw * (0.55 if first and f != "thumb" else 0.30)
            y1 = ln + (0.0 if k == 3 else rw * 0.12)
            V, F, UV, rim = lame(L @ A, rw * taper, rh * taper, y0, y1, 1.10 if not first else 1.04, tip=(k == 3), rows=rows, na=na)
            parts.append((b, V, F, UV, rim))
    # the knuckle plate: across the four _01 heads, on the back of the hand
    heads = np.array([G[f"{f}_01_{side}"][:3, 3] for f in FINGERS])
    backs = np.array([-G[f"{f}_02_{side}"][:3, 2] for f in FINGERS])
    along = np.array([G[f"{f}_02_{side}"][:3, 1] for f in FINGERS])
    rws = np.array([WIDTH[f] for f in FINGERS])
    e0 = heads[0] + (heads[0] - heads[1]) * 0.55
    e1 = heads[-1] + (heads[-1] - heads[-2]) * 0.55
    ctrl = np.vstack([e0, heads, e1])
    bk = np.vstack([backs[0], backs, backs[-1]]); bk /= np.linalg.norm(bk, axis=1, keepdims=True)
    al = np.vstack([along[0], along, along[-1]]); al /= np.linalg.norm(al, axis=1, keepdims=True)
    rr = np.r_[rws[0] * 0.8, rws, rws[-1] * 0.8]
    nseg = 4 if lod else 14
    s = np.linspace(0, len(ctrl) - 1, nseg + 1)
    def interp(a):
        return np.array([a[int(min(math.floor(x), len(a) - 2))] * (1 - (x - min(math.floor(x), len(a) - 2))) +
                         a[int(min(math.floor(x), len(a) - 2)) + 1] * (x - min(math.floor(x), len(a) - 2)) for x in s])
    pc, pb, pa, pr = interp(ctrl), interp(bk), interp(al), interp(rr[:, None])[:, 0]
    pb /= np.linalg.norm(pb, axis=1, keepdims=True); pa /= np.linalg.norm(pa, axis=1, keepdims=True)
    pts = pc + pb * (pr * TH * 0.95)[:, None]
    bumps = 0.45 * np.abs(np.cos(np.pi * (s - 1))) ** 2 * ((s > 0.6) & (s < len(ctrl) - 1.6))
    hz = np.full(len(s), 0.0062); ha = pr * 1.25  # (per point)
    taper = np.minimum(1.0, np.minimum(s, len(ctrl) - 1 - s) / 0.7 + 0.35)
    V, F, UV, rim = tube(pts, ha * taper, hz * taper, pa, pb, na=6 if lod else 10, bumps=bumps)
    parts.append((f"hand_{side}", V, F, UV, rim))
    # the cuff edge: a rolled rim round the mitten's wrist
    Hl = (np.linalg.inv(H) @ np.c_[P_hand, np.ones(len(P_hand))].T).T[:, :3]
    yc = float(np.percentile(Hl[:, 1], 3)) + 0.010
    ring = Hl[np.abs(Hl[:, 1] - yc) < 0.008]
    c = (ring.max(0) + ring.min(0)) / 2
    hx, hzz = (ring.max(0) - ring.min(0))[[0, 2]] / 2 + 0.0035
    nr = 10 if lod else 22
    pts, aa, bb, h1, h2 = [], [], [], [], []
    for i in range(nr):
        t = 2 * np.pi * i / nr
        p = np.array([c[0] + hx * math.cos(t), yc, c[2] + hzz * math.sin(t)])
        out = np.array([math.cos(t) / hx, 0, math.sin(t) / hzz]); out /= np.linalg.norm(out)
        pts.append(p); aa.append(np.array([0, 1.0, 0])); bb.append(out); h1.append(0.0045); h2.append(0.0034)
    pts = (H @ np.c_[np.array(pts), np.ones(nr)].T).T[:, :3]
    aa = (H[:3, :3] @ np.array(aa).T).T; bb = (H[:3, :3] @ np.array(bb).T).T
    V, F, UV, rim = tube(pts, np.array(h1), np.array(h2), aa, bb, closed=True, na=5 if lod else 8)
    parts.append((f"hand_{side}", V, F, UV, rim))
    return parts, yc


def normals(V, F):
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    return N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-12)


def assemble(parts, names):
    Vs, Fs, UVs, Js, Ns = [], [], [], [], []
    o = 0
    for bone, V, F, UV, rim in parts:
        Vs.append(V); Fs.append(F + o); UVs.append(UV); Ns.append(normals(V, F))
        Js.append(np.full(len(V), names.index(bone)))
        o += len(V)
    V = np.vstack(Vs); F = np.vstack(Fs)
    J = np.zeros((len(V), 4), np.uint16); J[:, 0] = np.concatenate(Js)
    W = np.zeros((len(V), 4), np.float32); W[:, 0] = 1
    return dict(pos=V.astype(np.float32), nrm=np.vstack(Ns).astype(np.float32), uv=np.vstack(UVs).astype(np.float32),
                J=J, W=W, idx=F.astype(np.uint32).ravel())


def id_map(size=128):
    """R = 4 * 32 + convexity (0..31): the lames' rims (v at either end of the band) and the back ridge worn bright,
    the knuckle plate's and cuff's band its rims; G/B/A free."""
    u = (np.arange(size) + 0.5) / size
    U, Vv = np.meshgrid(u, u)
    Vimg = 1 - Vv                                   # glTF v down from the image's top
    rimv = np.where(Vimg < UV_LAME, np.minimum(Vimg, UV_LAME - Vimg) / UV_LAME, np.minimum(Vimg - UV_LAME, 1 - Vimg) / (1 - UV_LAME))
    cv = 0.5 + 0.5 * np.clip(1 - rimv / 0.09, 0, 1)
    ridge = np.exp(-((U - 0.75) / 0.05) ** 2) * (Vimg < UV_LAME)
    cv = np.maximum(cv, 0.5 + 0.32 * ridge)
    side = np.exp(-((U - 0.0) / 0.04) ** 2) + np.exp(-((U - 1.0) / 0.04) ** 2) + np.exp(-((U - 0.5) / 0.04) ** 2)
    cv = np.maximum(cv, 0.5 + 0.2 * side * (Vimg < UV_LAME))
    r = (4 * 32 + np.clip(np.round(cv * 31), 0, 31)).astype(np.uint8)
    img = np.stack([r, np.full_like(r, 128), np.full_like(r, 128), np.full_like(r, 255)], -1)
    return Image.fromarray(img, "RGBA")


def albedo(size=256, seed=5):
    """The iron's light and dark (the shader takes its luminance and pulls the hue to the class's)."""
    rng = np.random.default_rng(seed)
    a = np.zeros((size, size))
    for cell, amp in ((64, 0.5), (24, 0.3), (8, 0.2)):
        n = rng.random((size // cell + 2, size // cell + 2))
        im = Image.fromarray((n * 255).astype(np.uint8)).resize((size + 2 * cell, size + 2 * cell), Image.BICUBIC)
        a += amp * np.asarray(im, float)[cell:cell + size, cell:cell + size] / 255
    v = 0.16 + 0.12 * a
    img = np.clip(np.stack([v, v * 0.98, v * 0.95], -1) * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(img, "RGB")


def png(im):
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


def write_glb(pkg, path, meshes, IBM_new):
    g = Glb(os.path.join(pkg, "body.glb"))
    j = g.j
    drop = [i for i, n in enumerate(j["nodes"]) if n.get("name", "").startswith("ford_warden") and n.get("name") != "ford_warden"]
    g.drop_nodes(drop)
    j["materials"], j["textures"], j["images"], j["samplers"] = [], [], [], []
    j["meshes"] = []
    ta = g.add_image(png(albedo()), "image/png", "gauntlet_albedo")
    j["materials"] = [{"name": "warden_gauntlet_iron", "pbrMetallicRoughness": {"baseColorTexture": {"index": ta},
                       "metallicFactor": 0.85, "roughnessFactor": 0.5}}]
    sk = j["skins"][0]
    sk["inverseBindMatrices"] = g.add_acc(IBM_new.transpose(0, 2, 1).reshape(-1, 16).astype(np.float32), "MAT4")
    arm = j["scenes"][0]["nodes"][0]
    body_node = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == "ford_warden")
    for k, (node_name, arr) in enumerate(meshes):
        a = {"POSITION": g.add_acc(arr["pos"], "VEC3", minmax=True), "NORMAL": g.add_acc(arr["nrm"], "VEC3"),
             "TEXCOORD_0": g.add_acc(arr["uv"], "VEC2"), "JOINTS_0": g.add_acc(arr["J"], "VEC4"),
             "WEIGHTS_0": g.add_acc(arr["W"], "VEC4")}
        j["meshes"].append({"name": node_name, "primitives": [{"attributes": a, "indices": g.add_acc(arr["idx"], "SCALAR", target=34963),
                                                               "material": 0, "mode": 4}]})
        if k == 0:
            j["nodes"][body_node] = {"name": node_name, "mesh": 0, "skin": 0}
        else:
            j["nodes"].append({"name": node_name, "mesh": k, "skin": 0})
            j["nodes"][arm].setdefault("children", []).append(len(j["nodes"]) - 1)
    g.save(path)
    log(f"wrote {path} ({os.path.getsize(path) / 1e3:.0f} kB)")


def hand_verts(g, names, side):
    """The 'generated' primitive's vertices mostly on this hand (hand + fingers weight > 0.5), and their positions."""
    out = []
    for mesh in g.j["meshes"]:
        for p in mesh["primitives"]:
            if g.j["materials"][p["material"]]["name"] != "generated":
                continue
            P = g.acc(p["attributes"]["POSITION"]).astype(np.float32)
            J = g.acc(p["attributes"]["JOINTS_0"]); W = g.acc(p["attributes"]["WEIGHTS_0"])
            bones = [i for i, n in enumerate(names) if n.endswith("_" + side) and n.split("_")[0] in ("hand",) + FINGERS + ("thumb",)]
            w = sum((W * (J == b)).sum(1) for b in bones)
            out.append(P[w > 0.5])
    return np.vstack(out)


def main():
    pkg = PKG
    if "--pkg" in sys.argv:
        pkg = os.path.abspath(sys.argv[sys.argv.index("--pkg") + 1])
    g = Glb(os.path.join(pkg, "body.glb"))
    names, IBM, G = skeleton(g)
    fix = fixed_rests(G)
    G.update(fix)
    IBM_new = IBM.copy()
    for n, M in fix.items():
        IBM_new[names.index(n)] = np.linalg.inv(M)
    full, lod1, info, ycut = [], [], {}, {}
    for side in "lr":
        Ph = hand_verts(g, names, side)
        p, yc = hand_parts(side, G, Ph)
        pl, _ = hand_parts(side, G, Ph, lod=True)
        full += p; lod1 += pl
        # the knuckle line in hand-local y (the four _01 heads), the mitten hidden past it
        H = np.linalg.inv(G[f"hand_{side}"])
        ycut[side] = min(float((H @ G[f"{f}_01_{side}"])[1, 3]) for f in FINGERS) + CUT
    A, Al = assemble(full, names), assemble(lod1, names)
    os.makedirs(os.path.join(pkg, "armor"), exist_ok=True)
    write_glb(pkg, os.path.join(pkg, "armor", "gauntlets.glb"), [("gauntlets.iron", A), ("gauntlets.lod1.iron", Al), ("gauntlets.shadow", Al)], IBM_new)
    id_map().save(os.path.join(pkg, "armor", "gauntlets_id.png"))
    # the tuck: body.glb's and lod.glb's hand vertices past the knuckle line
    keys = set()
    for fname in ("body.glb", "lod.glb"):
        gg = Glb(os.path.join(pkg, fname))
        nm = [gg.j["nodes"][n]["name"] for n in gg.j["skins"][0]["joints"]]
        cnt = 0
        for side in "lr":
            P = hand_verts(gg, nm, side)
            Hl = (np.linalg.inv(G[f"hand_{side}"]) @ np.c_[P.astype(float), np.ones(len(P))].T).T
            sel = P[Hl[:, 1] > ycut[side]]
            cnt += len(sel)
            for v in sel:
                keys.add(tuple(int(round(float(c) * 1e5)) for c in v))
        info[fname] = cnt
    with open(os.path.join(pkg, "armor", "gauntlets_tuck.bin"), "wb") as f:
        f.write(struct.pack("<i", len(keys)))
        for x, y, z in sorted(keys):
            f.write(struct.pack("<iiif", x, y, z, 0.0))
    tris = len(A["idx"]) // 3
    log(json.dumps({"tris": tris, "lodTris": len(Al["idx"]) // 3, "tuckPoints": len(keys), "tuckByFile": info,
                    "knuckleCut": {k: round(v, 4) for k, v in ycut.items()}}))
    return tris, len(Al["idx"]) // 3


if __name__ == "__main__":
    main()
