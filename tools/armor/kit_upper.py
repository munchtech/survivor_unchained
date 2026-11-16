"""The kit's upper pieces (lane D, 16 Nov 2026): pauldrons and helm, for tools/armor/kit_build.py (build.json
"module": "kit_upper": this module's own build, as kit_limbs).

    python tools/armor/kit_build.py kit_pauldrons
    python tools/armor/kit_build.py kit_helm

Both are RIGID BY CLEARANCE (metal need not swing; the spaulder's motion fit is not reopened): every plate stands off
a dilated, smoothed envelope of what is under it, so no pose's skin reaches it. A rigid group is ONE node with one
primitive per material (steel, gold, leather), so the install gives plate, rims and rivets one blend (a node per
material would give each its own mean blend: the rims would drift off the plate in motion).

pauldrons  per side: a cop (a dome from the upper arm's joint round the up-out pole, outline alpha_max(beta) in the
           build.json), a small upturned ridge on its neck-side edge, two lames on the upper arm (a cylinder chart
           round the arm's axis, each under the one above), gold rolled rims, gold rivets; a brown strap round the
           upper arm with a gold buckle (the strap bends with her: it is leather on her skin).
           Groups: cop (her shoulder's blend), lames + buckle (the upper arm's blend), strap (skinned).
helm       an open-face helm round her head AND her braid's hair cap (rays from inside her head, the outer of head and
           hair), a face opening that never covers eyes, nose or mouth, cheek guards, a crest, a gold brow band with a
           knot-work braid of two crossing beads, gold rims, rivets. Hair kept (piece "hair": "keep"): the braid falls
           from under the back rim.
Every measure is in the piece's build.json.
"""
import hashlib
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_build as kb  # noqa: E402
import kit_hips as kh  # noqa: E402
from native_build import Part, U, buckle, grid_tris, raycast, rivet, vertex_normals  # noqa: E402

PEOPLE = os.path.join(kb.REPO, "godot", "art", "people")


# ---------------------------------------------------------------- helpers

def icosphere(n):
    t = (1 + 5 ** 0.5) / 2
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                  [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    F = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2],
                  [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11],
                  [6, 2, 10], [8, 6, 7], [9, 8, 1]])
    V = U(V)
    for _ in range(n):
        V, F = kh.subdivide(V, F)
        V = U(V)
    return V, F


def mesh_of(path, node):
    from heroine_neck import _Gl
    G = _Gl(path)
    g = G.g
    nd = [x for x in g["nodes"] if x.get("name") == node][0]
    Vs, Fs, o = [], [], 0
    for p in g["meshes"][nd["mesh"]]["primitives"]:
        X = G.get(p["attributes"]["POSITION"]).astype(float)
        Vs.append(X)
        Fs.append(G.get(p["indices"]).reshape(-1, 3).astype(int) + o)
        o += len(X)
    return np.vstack(Vs), np.vstack(Fs)


def ring_max(rho, F, it):
    """rho dilated over `it` rings of the mesh (each point the max of its neighbours)."""
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    r = rho.copy()
    for _ in range(it):
        m = r.copy()
        np.maximum.at(m, E[:, 0], r[E[:, 1]])
        r = m
    return r


def smooth_scalar(r, F, it, lam=0.5):
    return kh.laplace(r[:, None], F, it, lam=lam)[:, 0]


def fill_nan(rho, F):
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    r = rho.copy()
    for _ in range(200):
        bad = ~np.isfinite(r)
        if not bad.any():
            break
        s = np.zeros(len(r))
        c = np.zeros(len(r))
        ok = np.isfinite(r[E[:, 1]])
        np.add.at(s, E[ok, 0], r[E[ok, 1]])
        np.add.at(c, E[ok, 0], 1)
        fix = bad & (c > 0)
        r[fix] = s[fix] / c[fix]
    return r


def cast_union(O, D, meshes, tmax):
    """Per ray the OUTERMOST of the first hits on each mesh (her hair over her scalp): t, nan where none."""
    T = np.full(len(D), np.nan)
    for V, F in meshes:
        t, _ = raycast(V, F, np.broadcast_to(O, D.shape).copy() if np.ndim(O) == 1 else O, D, tmax, chunk=48)
        T = np.fmax(T, t)
    return T


def interp_table(tab, x):
    tab = np.asarray(tab, float)
    return np.interp(x, tab[:, 0], tab[:, 1])


def path_bead(name, mat, E, nref, rim, off, closed):
    return kb.bead(nref, name, mat, E, rim, off, closed)


def loops_ordered(P, F):
    return [P[L] for L in kh.boundary_loops(F)]


def mirror(p, name):
    q = Part(name, p.material, p.P * [-1, 1, 1], p.T[:, ::-1], p.uv0, p.uv1, p.col,
             p.N * [-1, 1, 1])
    return q


# ---------------------------------------------------------------- dome shell (cop, helm)

class Dome:
    """A shell over rays from a centre O along unit directions D (an icosphere's points): skin distance t, envelope
    rho (dilated, smoothed, + clear), the shell's inner points P = O + D rho."""

    def __init__(self, O, Vs, Fs, keep, meshes, tmax, dil, smooth_it, clear):
        self.O = np.asarray(O, float)
        Vk = np.nonzero(keep)[0]
        remap = -np.ones(len(Vs), int)
        remap[Vk] = np.arange(len(Vk))
        Fk = Fs[keep[Fs].all(1)]
        self.D, self.F = Vs[Vk], remap[Fk]
        self.t = cast_union(self.O, self.D, meshes, tmax)
        r = fill_nan(self.t, self.F)
        r = ring_max(r, self.F, dil)
        r = smooth_scalar(r, self.F, smooth_it)
        self.rho = np.maximum(r, fill_nan(self.t, self.F)) + clear
        self.P = self.O + self.D * self.rho[:, None]

    def cut(self, g):
        """The shell patch where g > 0 (g per point), cut on its edges; its outward directions."""
        V, F = kh.clip(self.P, self.F, g)
        V, F = kh.weld(V, F)
        N = vertex_normals(V, F)
        N = np.where(((N * (V - self.O)).sum(1) < 0)[:, None], -N, N)
        return V, F, U(N)


# ---------------------------------------------------------------- pauldrons

def arm_frame(ref, side="l"):
    c = ref.joints[f"upperarm_{side}"]
    a = U(ref.joints[f"lowerarm_{side}"] - c)
    up = np.array([0.0, 1.0, 0.0])
    e = U(up - (up @ a) * a)
    f = U(np.cross(a, e))
    if f[2] < 0:
        f = -f
    return c, a, e, f


def pauldrons(cfg, ref):
    gold, steel, leath = cfg["mat"]["trim"], cfg["mat"]["plate"], cfg["mat"]["strap"]
    rim, ck, lk = cfg["rim"], cfg["cop"], cfg["lames"]
    c, a, e, f = arm_frame(ref)
    near = ref.T[(np.linalg.norm(ref.V[ref.T].mean(1) - c, axis=1) < 0.24)]
    body = [(ref.V, near)]
    # ---- the cop: rays from inside her shoulder round the up-out pole e
    Vs, Fs = icosphere(ck.get("subdiv", 5))
    O = c - e * ck["sink"]
    alpha = np.degrees(np.arccos(np.clip(Vs @ e, -1, 1)))
    beta = np.degrees(np.arctan2(Vs @ f, Vs @ -a))
    keep = alpha < ck["chart_deg"]
    dome = Dome(O, Vs, Fs, keep, body, 0.25, ck["dilate"], ck["smooth"], ck["clear"])
    al = np.degrees(np.arccos(np.clip(dome.D @ e, -1, 1)))
    be = np.degrees(np.arctan2(dome.D @ f, dome.D @ -a))
    amax = interp_table(ck["outline"], np.abs(be))
    g = amax - al
    V, F, N = dome.cut(g)
    th = cfg["thick"]
    cop = kh.shell("cop", steel, V, F, N, th)
    nref = kh.Normals(V + N * th, N)
    G = {"cop": [cop], "cop_gold": [], "lames": [], "lames_gold": [], "strap": []}
    for L in loops_ordered(V + N * (th * 0.5), F):
        G["cop_gold"].append(path_bead("cop_rim", gold, L, nref, rim, 0.0, True))

    def on_cop(al_, be_, lift):
        d = U(np.cos(np.radians(al_))[:, None] * e + np.sin(np.radians(al_))[:, None] *
              (np.cos(np.radians(be_))[:, None] * -a + np.sin(np.radians(be_))[:, None] * f))
        t = cast_union(O, d, [(V + N * th, F)], 0.3)
        ok = np.isfinite(t)
        return O + d[ok] * t[ok, None], d[ok], ok
    # rivets along the rim
    rv = ck["rivets"]
    bb = np.arange(-rv["beta"], rv["beta"] + 1e-6, rv["step"])
    pts, d, _ = on_cop(interp_table(ck["outline"], np.abs(bb)) - rv["in_deg"], bb, 0)
    for p in pts:
        q, n, _ = nref.closest(p[None])
        G["cop_gold"].append(rivet(p, n[0], r=rv["r"], h=rv["h"], name="cop_rivet", material=gold))
    # the upturned ridge on the neck-side edge
    rd = ck["ridge"]
    bb = np.linspace(-rd["beta"], rd["beta"], 41)
    base, d, ok = on_cop(interp_table(ck["outline"], np.abs(bb)) - rd["in_deg"], bb, 0)
    bb = bb[ok]
    q, n, _ = nref.closest(base)
    h = rd["h"] * np.sin(np.pi * np.clip((bb + rd["beta"]) / (2 * rd["beta"]), 0, 1)) ** 0.6
    lean = U(n + (-a) * rd["lean"])
    top = base + lean * h[:, None]
    tg = U(np.gradient(base, axis=0))
    side = U(np.cross(tg, lean))
    R = 2
    Pin = np.stack([base - n * 0.0005, top], 0)
    Pin = Pin - side[None] * rd["thick"] / 2
    G["cop"].append(kb.slab("cop_ridge", steel, Pin, np.repeat(side[None], R, 0), rd["thick"]))
    G["cop_gold"].append(path_bead("cop_ridge_rim", gold, top + lean * 0.0008, kh.Normals(top, lean),
                                   {**rim, "w": rd["rim_w"], "h": rd["rim_h"]}, 0.0, False))
    # ---- the lames: a cylinder chart round the arm's axis
    C = lk["cols"]
    thd = np.linspace(-lk["theta"], lk["theta"], C)
    thr = np.radians(thd)
    rad = np.cos(thr)[:, None] * e + np.sin(thr)[:, None] * f
    for k, lm in enumerate(lk["rows"]):
        Rn = lm["n"]
        s0, s1 = lm["s"]
        dip = lm["dip"] * np.cos(np.radians(thd) * 90.0 / lk["theta"])
        S = np.linspace(0, 1, Rn)[:, None] * (s1 + dip - s0)[None, :] + s0
        Oa = c[None, None] + S[..., None] * a
        Dd = np.broadcast_to(rad[None], (Rn, C, 3)).copy()
        t = cast_union(Oa.reshape(-1, 3), Dd.reshape(-1, 3).copy(), body, 0.2).reshape(Rn, C)
        t = kb.fill_rows(t)
        from scipy.ndimage import grey_dilation
        r = grey_dilation(t, size=(lm["dil"], lm["dil"]))
        r = kb.gsmooth(r, (1.5, 2.0), False)
        r = np.maximum(r, t) + lm["clear"] + lm["flare"] * np.linspace(0, 1, Rn)[:, None] ** 2
        Pin = Oa + Dd * r[..., None]
        lame = kb.slab(f"lame{k}", steel, Pin, Dd.copy(), th)
        G["lames"].append(lame)
        Pout = Pin + Dd * (th * 0.5)
        E = np.vstack([Pout[::-1, 0], Pout[-1, 1:], Pout[-2::-1, -1]])
        G["lames_gold"].append(path_bead(f"lame{k}_rim", gold, E, kh.Normals(Pout.reshape(-1, 3), Dd.reshape(-1, 3)),
                                         rim, 0.0, False))
        for j in (2, C - 3):
            p = Pin[Rn // 2, j] + Dd[Rn // 2, j] * (th + 0.0003)
            G["lames_gold"].append(rivet(p, Dd[Rn // 2, j], r=lk["rivet_r"], h=lk["rivet_h"], name="lame_rivet",
                                         material=gold))
    # ---- the strap round the upper arm (leather on her skin) and its buckle
    sk = cfg["strap"]
    Cs = 72
    tha = np.radians(np.linspace(0, 360, Cs, endpoint=False))
    rads = np.cos(tha)[:, None] * e + np.sin(tha)[:, None] * f
    S = np.linspace(sk["s"], sk["s"] + sk["w"], 5)
    Dd = np.broadcast_to(rads[None], (len(S), Cs, 3)).copy()
    Oa = np.broadcast_to(c[None, None] + S[:, None, None] * a, Dd.shape).copy()
    t = cast_union(Oa.reshape(-1, 3), Dd.reshape(-1, 3), body, 0.2).reshape(len(S), Cs)
    t = kb.gsmooth(kb.fill_rows(t), (0.0, 1.0), True)
    Pin = Oa + Dd * (t + sk["clear"])[..., None]
    G["strap"].append(kb.slab("strap", leath, Pin, Dd, sk["thick"], closed_c=True))
    jb = int(round(sk["buckle_deg"] / 360 * Cs)) % Cs
    pb = Pin[2, jb] + Dd[2, jb] * sk["thick"]
    G["lames_gold"].append(buckle(pb, Dd[2, jb], a, w=sk["w"] * 1.25, h=sk["w"] * 1.0, bar=0.0024, name="strap_buckle",
                                  material=gold))
    nodes = {"pauldron_cop_l_rigid": G["cop"] + G["cop_gold"], "pauldron_lames_l_rigid": G["lames"] + G["lames_gold"],
             "pauldron_strap_l": G["strap"]}
    out = {}
    for nm, ps in nodes.items():
        by = {}
        for p in ps:
            by.setdefault(p.material, []).append(p)
        L = [Part.join(nm, m, q) for m, q in by.items()]
        out[nm] = L
        rn = nm.replace("_l_rigid", "_r_rigid") if nm.endswith("_l_rigid") else nm[:-2] + "_r"
        out[rn] = [mirror(p, rn) for p in L]
    return out


# ---------------------------------------------------------------- helm

def helm(cfg, ref):
    gold, steel = cfg["mat"]["trim"], cfg["mat"]["plate"]
    rim, hk = cfg["rim"], cfg["helm"]
    body = os.path.join(PEOPLE, "heroine.glb")
    head = mesh_of(body, "HeroineHead")
    hv, hf = mesh_of(os.path.join(PEOPLE, f"{hk['hair']}.gltf"), hk["hair_node"])
    hc = hv[hf].mean(1)
    hair = (hv, hf[hc[:, 1] > hk["hair_above"]])
    O = np.array(hk["centre"], float)
    Vs, Fs = icosphere(hk.get("subdiv", 5))
    keep = Vs[:, 1] > -0.75
    dome = Dome(O, Vs, Fs, keep, [head, hair], 0.3, hk["dilate"], hk["smooth"], hk["clear"])
    P0 = O + dome.D * fill_nan(dome.t, dome.F)[:, None]  # (her head / hair under each ray)
    x, y, z = P0[:, 0], P0[:, 1], P0[:, 2]
    psi = np.degrees(np.arctan2(np.abs(dome.D[:, 0]), dome.D[:, 2]))  # 0 front, 90 her side, 180 back
    ybot = interp_table(hk["bottom"], psi)
    fo = hk["face"]
    ax = np.abs(x)
    brow = fo["brow"] - fo["peak_drop"] * np.clip(1 - ax / fo["peak_w"], 0, 1) ** 1.5
    half = interp_table(fo["half_w"], y)
    s_face = np.minimum(brow - y, half - ax)  # > 0 inside the face opening (front only)
    s_face = np.where(z > fo["z_min"], s_face, -1.0)
    g = np.minimum(y - ybot, -s_face)
    V, F, N = dome.cut(g)
    th = cfg["thick"]
    shell = kh.shell("helm", steel, V, F, N, th)
    Pout = V + N * th
    nref = kh.Normals(Pout, N)
    S, Gd = [shell], []
    for L in loops_ordered(V + N * (th * 0.5), F):
        Gd.append(path_bead("helm_rim", gold, L, nref, rim, 0.0, True))

    def surf_pts(D):
        D = U(np.asarray(D, float))
        t = cast_union(O, D, [(Pout, F)], 0.3)
        ok = np.isfinite(t)
        return O + D[ok] * t[ok, None], ok

    # crest: a keel front to back over the top
    cr = hk["crest"]
    ang = np.radians(np.linspace(cr["from"], cr["to"], 60))
    D = np.c_[np.zeros_like(ang), np.cos(ang), np.sin(ang)]
    base, ok = surf_pts(D)
    q, n, _ = nref.closest(base)
    w = np.sin(np.pi * np.linspace(0, 1, len(base))) ** 0.35
    top = base + n * (cr["h"] * w)[:, None]
    side = np.tile([1.0, 0, 0], (len(base), 1))
    Pin = np.stack([base - n * 0.0006, top], 0) - side[None] * cr["w"] / 2
    S.append(kb.slab("crest", steel, Pin, np.repeat(side[None], 2, 0), cr["w"]))
    Gd.append(path_bead("crest_rim", gold, top, kh.Normals(top, n), {**rim, "w": cr["rim_w"], "h": cr["rim_h"]}, 0.0, False))
    # brow band: a gold band over the forehead, a braid of two crossing beads on it
    bd = hk["band"]
    ps = np.radians(np.linspace(-bd["psi"], bd["psi"], 90))

    def band_line(dy):
        out = []
        for p_ in ps:
            yy = bd["y"] + dy + bd["rise"] * (np.degrees(abs(p_)) / bd["psi"]) ** 2
            el = np.arctan2(yy - O[1], 0.09)
            out.append([np.sin(p_) * np.cos(el), np.sin(el), np.cos(p_) * np.cos(el)])
        P, ok = surf_pts(np.array(out))
        return P
    lo, hi = band_line(-bd["h"] / 2), band_line(bd["h"] / 2)
    m = min(len(lo), len(hi))
    lo, hi = lo[:m], hi[:m]
    nb = nref.closest(0.5 * (lo + hi))[1]
    Pin = np.stack([lo, 0.5 * (lo + hi), hi], 0) + nb[None] * 0.0002
    S_band = kb.slab("band", gold, Pin, np.repeat(nb[None], 3, 0), bd["thick"])
    Gd.append(S_band)
    Bo = Pin + nb[None] * bd["thick"]
    bref = kh.Normals(Bo.reshape(-1, 3), np.repeat(nb[None], 3, 0).reshape(-1, 3))
    s = np.linspace(0, 1, m)
    for ph in (0.0, np.pi):
        wv = 0.5 + 0.38 * np.sin(2 * np.pi * bd["waves"] * s + ph)
        E = lo + (hi - lo) * wv[:, None] + nb * bd["thick"]
        Gd.append(path_bead("band_knot", gold, E, bref, {**rim, "w": bd["knot_w"], "h": bd["knot_h"], "step": 0.003}, 0.0, False))
    # rivets along the cheek guards and the back rim
    for rv in hk["rivets"]:
        D = np.array([[np.sin(np.radians(p_)) * np.cos(np.radians(el)), np.sin(np.radians(el)), np.cos(np.radians(p_)) * np.cos(np.radians(el))]
                      for p_, el in rv])
        pts, ok = surf_pts(D)
        for p in pts:
            n = nref.closest(p[None])[1][0]
            for sg in (1, -1):
                pp = p * [sg, 1, 1]
                nn = n * [sg, 1, 1]
                if sg < 0 and abs(p[0]) < 1e-3:
                    continue
                Gd.append(rivet(pp, nn, r=hk["rivet_r"], h=hk["rivet_h"], name="helm_rivet", material=gold))
    by = {}
    for p in S + Gd:
        by.setdefault(p.material, []).append(p)
    return {"helm_rigid": [Part.join("helm_rigid", mm, q) for mm, q in by.items()]}, [head, hair]


# ---------------------------------------------------------------- build

def write_multi(path, groups, extras):
    """groups {node name: [Part, ..]} -> a .glb: one node a group, one primitive a material."""
    import gear_native as gn
    nodes, key = [], []
    for nm, ps in groups.items():
        for k, p in enumerate(ps):
            nd = p.node()
            nd["name"] = f"{nm}#{k}"
            nodes.append(nd)
    gn.write_glb(path, nodes, extras)
    b = open(path, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    blob = b[20 + jl + 8:]
    meshes, out_nodes = [], []
    for nm in groups:
        prims = []
        for i, n in enumerate(js["nodes"]):
            if n["name"].split("#")[0] == nm:
                prims += js["meshes"][n["mesh"]]["primitives"]
        meshes.append({"name": nm, "primitives": prims})
        out_nodes.append({"name": nm, "mesh": len(meshes) - 1})
    js["meshes"], js["nodes"] = meshes, out_nodes
    js["scenes"] = [{"nodes": list(range(len(out_nodes)))}]
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 28 + len(jb) + len(blob)))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A) + jb)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + blob)


def build(pid, cfg=None):
    d = os.path.join(kb.SRC, pid)
    cfg = cfg or json.load(open(os.path.join(d, "build.json"), encoding="utf-8"))
    mats = json.load(open(kb.MATS, encoding="utf-8"))
    for m in cfg["mat"].values():
        assert m in mats, f"material {m} not in outfit_materials.json"
    ref = kb.her_a()
    if cfg["recipe"] == "helm":
        groups, under = helm(cfg, ref)
        from native_build import Ref
        V = np.vstack([under[0][0], under[1][0]])
        T = np.vstack([under[0][1], under[1][1] + len(under[0][0])])
        cref = Ref(V, T)
    else:
        groups = pauldrons(cfg, ref)
        cref = ref
    pushed = 0
    for nm, ps in groups.items():
        if nm.endswith("_rigid"):
            continue
        for p in ps:  # (a bending part: never closer than clear_min)
            for _ in range(4):
                cc = kb.clearance(cref, p)
                q, n, _ = cref.closest(p.P)
                low = cc < cfg["clear_min"]
                if not low.any():
                    break
                p.P[low] += n[low] * (cfg["clear_min"] - cc[low] + 0.0001)[:, None]
                pushed += int(low.sum())
    for ps in groups.values():
        for p in ps:
            p.N = vertex_normals(p.P, p.T)
    write_multi(os.path.join(d, f"{pid}.glb"), groups, {"kit_build": {"piece": pid}})
    piece = {k: v for k, v in cfg["piece"].items() if k != "layer"}
    piece = {"id": piece["id"], "name": piece["name"], "slot": piece["slot"], "style": "mesh",
             "params": {"file": f"{pid}.glb"}, **{k: v for k, v in piece.items() if k not in ("id", "name", "slot")},
             "layer": cfg["piece"].get("layer", 1), "body_sha1": hashlib.sha1(open(kb.BODY, "rb").read()).hexdigest()}
    with open(os.path.join(d, "piece.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(piece, f, indent=1)
        f.write("\n")
    rep = {"tris": int(sum(len(p.T) for ps in groups.values() for p in ps)),
           "by_node": {nm: {p.material: int(len(p.T)) for p in ps} for nm, ps in groups.items()}, "pushed_to_min": pushed,
           "min_clear_mm": {f"{nm}.{p.material}": round(float(kb.clearance(cref, p).min()) * 1000, 2)
                            for nm, ps in groups.items() for p in ps}}
    print(json.dumps(rep, indent=1))
    return rep


if __name__ == "__main__":
    build(sys.argv[1])
