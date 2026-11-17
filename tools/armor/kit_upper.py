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

SWEEP_CLIPS = ("idle_warden", "run_warden", "sword_heavy", "leap")   # the demo's clips (docs/handoff/armor.md, lead 2)
HAND_PARTS = ("lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb")


def _hinge_key(ride):
    """The helper hinges' spec when a ride names a hinge bone (its amount moves that frame: pauldron-2 r4, 16 Nov, a
    pauldron_hinge .5 -> .8 change kept the stale rooms), else [] (every other cache keeps its key)."""
    if not any("hinge" in b for b in ride):
        return []
    sys.path.insert(0, os.path.join(kb.REPO, "tools", "anim"))
    import helpers as hp
    return [hp.SPEC.get("hinges")]


def sweep_room(bone, centre, radius, clips=SWEEP_CLIPS, vox=0.002, verbose=True, exclude=None):
    """The room a rigid plate riding `bone` (left side) needs: her skin within `radius` of `centre` (rest), over her rest
    and every frame of the demo clips, carried back into that bone's rest frame; the right side's (mirrored onto the
    left) joined in, so one mirrored design clears both arms. Hands and forearms left out (they swing past). Every
    triangle sampled at its corners, edge middles and centre, reduced to the outermost point per `vox` cell. Cached by
    its inputs (git-ignored .shots). Returns points [n, 3] at her rest, left side.
    `exclude` (sweep "exclude", armor-D r7 17 Nov, body B): {"bones": [name prefixes], "w": weight} leaves out her skin
    whose weight on those bones (side-free prefixes, e.g. "breast", "spine_") is at least w: B's bust sits inside the
    sweep radius, and carried into the arm's frame over the clips it filled the room in front of the shoulder (cop bite
    144 mm, lame0 needing 120-134 mm lift at the front); unset = every skin point (A, unchanged)."""
    sys.path.insert(0, os.path.join(kb.REPO, "tools", "anim"))
    main = os.path.abspath(os.path.join(kb.REPO, "..", "..", ".."))   # (as wearcheck: the main checkout's built clips)
    os.environ.setdefault("ANIM_OUT", os.path.join(main if os.path.isdir(os.path.join(main, "tools", "anim", "out"))
                                                   else kb.REPO, "tools", "anim", "out"))
    import skin
    __import__("bodies").clip_source(skin)   # (p1: B's own clips, never A's built ones; A: unchanged)
    if not (skin.OUT / "clips").is_dir():
        from pathlib import Path
        skin.OUT = Path(os.path.join(main, "tools", "anim", "out"))
    kb.require_body_inputs(clips)
    deps = [kb.body_glb()] + [str(skin.OUT / "clips" / f"{c}.json") for c in clips]
    stamp = [(os.path.basename(p), os.path.getsize(p), int(os.path.getmtime(p))) for p in deps]
    # (`bone`: one bone, or a blend {bone: weight} as a rigid_ride gives (the plate's frame is the blend of their skin
    # matrices, as Godot's linear blend poses it))
    ride = {bone: 1.0} if isinstance(bone, str) else {k: float(v) for k, v in sorted(bone.items())}
    key = hashlib.sha1(json.dumps(["v1", bone if isinstance(bone, str) else sorted(ride.items()),
                                   [round(float(v), 5) for v in centre], radius, list(clips), vox,
                                   stamp] + _hinge_key(ride)
                                  + ([["ex", sorted(exclude["bones"]), float(exclude.get("w", 0.5))]] if exclude else [])
                                  ).encode()).hexdigest()[:14]
    cache = os.path.join(kb.CACHE, f"paul_sweep_{key}.npz")
    if os.path.exists(cache):
        return np.load(cache)["P"]
    sk = skin.Skeleton.load(__import__("bodies").skeleton_path())
    body = skin.Body(sk, [(skin.Path(kb.body_glb()), lambda n: n == "Heroine", "skin")], skin.Jiggle(sk, 1, 1),
                     label="her", helpers=True)
    names = list(body.sk.names)
    hand = np.array([str(n).startswith(HAND_PARTS) for n in names] + [False] * 64)
    hw = (body.W * hand[np.minimum(body.Jv, len(hand) - 1)]).sum(1)
    if exclude:
        exb = np.array([str(n).startswith(tuple(exclude["bones"])) for n in names] + [False] * 64)
        hw = np.where((body.W * exb[np.minimum(body.Jv, len(exb) - 1)]).sum(1) >= float(exclude.get("w", 0.5)), 1.0, hw)
    out = []
    for side, sgn in (("l", 1.0), ("r", -1.0)):
        c = np.asarray(centre, float) * [sgn, 1, 1]
        near = np.linalg.norm(body.P - c, axis=1) < radius
        sel = near[body.T].all(1) & (hw[body.T] < 0.05).all(1)
        T = body.T[sel]
        idx, Tl = np.unique(T, return_inverse=True)
        Tl = Tl.reshape(T.shape)
        E_ = np.unique(np.sort(np.r_[Tl[:, [0, 1]], Tl[:, [1, 2]], Tl[:, [2, 0]]], 1), axis=0)
        bw = [(names.index(k[:-2] + "_" + side), w) for k, w in ride.items()]

        def samples(P):
            return np.vstack([P, (P[E_[:, 0]] + P[E_[:, 1]]) / 2, P[Tl].mean(1)])
        # (per vox cell keep one point: the room is the cloud's outer hull from the plate's side; a cell's points are
        # within vox of each other, so any one serves)
        def reduce(X):
            _, first = np.unique(np.floor(X / vox).astype(np.int64), axis=0, return_index=True)
            return X[first]
        acc = samples(body.P[idx])
        for cl in clips:
            pts = [acc]
            for G in body.frames(body.clip(cl)):
                S = body.skin_mats(G)
                Mi = np.linalg.inv(sum(w * S[b] for b, w in bw))
                pts.append(samples(body.pose(G, idx)) @ Mi[:3, :3].T + Mi[:3, 3])
            acc = reduce(np.vstack(pts))
            if verbose:
                print(f"sweep_room {side} {cl} {len(acc)} pts", flush=True)
        out.append(acc * [sgn, 1, 1])
    P = np.vstack(out)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.savez_compressed(cache, P=P)
    return P


def pose_frame(ride, centre, radius, clip, frame=0, rest=False):
    """Her skin within `radius` of `centre` (rest, left side, no hands) in one frame of a clip, carried into the rest
    frame of a rigid plate riding the blend `ride` ({bone: weight}, as its rigid_ride), with her upper arm's joint, its
    direction and world up in that frame: a plate built round these fits her in that pose (and rides from there).
    Cached by its inputs (git-ignored .shots). Returns P [n, 3], T [m, 3], joint, arm direction, up (and with `rest`
    the same points at her rest, P0 [n, 3]: the liner's skin)."""
    sys.path.insert(0, os.path.join(kb.REPO, "tools", "anim"))
    main = os.path.abspath(os.path.join(kb.REPO, "..", "..", ".."))
    os.environ.setdefault("ANIM_OUT", os.path.join(main if os.path.isdir(os.path.join(main, "tools", "anim", "out"))
                                                   else kb.REPO, "tools", "anim", "out"))
    import skin
    __import__("bodies").clip_source(skin)   # (p1: B's own clips, never A's built ones; A: unchanged)
    if not (skin.OUT / "clips").is_dir():
        from pathlib import Path
        skin.OUT = Path(os.path.join(main, "tools", "anim", "out"))
    kb.require_body_inputs([clip])
    deps = [kb.body_glb(), str(skin.OUT / "clips" / f"{clip}.json")]
    stamp = [(os.path.basename(p), os.path.getsize(p), int(os.path.getmtime(p))) for p in deps]
    key = hashlib.sha1(json.dumps(["pf1", sorted((k, round(float(v), 5)) for k, v in ride.items()),
                                   [round(float(v), 5) for v in centre], radius, clip, frame, stamp]
                                  + _hinge_key(ride)).encode()).hexdigest()[:14]
    cache = os.path.join(kb.CACHE, f"paul_pose_{key}.npz")
    if os.path.exists(cache):
        z = np.load(cache)
        if not rest:
            return z["P"], z["T"], z["c"], z["a"], z["up"]
        if "P0" in z:
            return z["P"], z["T"], z["c"], z["a"], z["up"], z["P0"]
    sk = skin.Skeleton.load(__import__("bodies").skeleton_path())
    body = skin.Body(sk, [(skin.Path(kb.body_glb()), lambda n: n == "Heroine", "skin")], skin.Jiggle(sk, 1, 1),
                     label="her", helpers=True)
    names = list(body.sk.names)
    hand = np.array([str(n).startswith(HAND_PARTS) for n in names] + [False] * 64)
    hw = (body.W * hand[np.minimum(body.Jv, len(hand) - 1)]).sum(1)
    G = body.frames(body.clip(clip))[frame]
    S = body.skin_mats(G)
    Mi = np.linalg.inv(sum(w * S[names.index(b)] for b, w in ride.items()))
    near = np.linalg.norm(body.P - np.asarray(centre, float), axis=1) < radius
    sel = near[body.T].all(1) & (hw[body.T] < 0.05).all(1)
    idx, T = np.unique(body.T[sel], return_inverse=True)
    T = T.reshape(-1, 3)
    P = body.pose(G, idx) @ Mi[:3, :3].T + Mi[:3, 3]

    def joint(n):
        return Mi[:3, :3] @ G[names.index(n)][:3, 3] + Mi[:3, 3]
    c = joint("upperarm_l")
    a = U(joint("lowerarm_l") - c)
    up = U(Mi[:3, :3] @ np.array([0.0, 1.0, 0.0]))
    P0 = np.asarray(body.P[idx], float)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.savez_compressed(cache, P=P, T=T, c=c, a=a, up=up, P0=P0)
    return (P, T, c, a, up, P0) if rest else (P, T, c, a, up)


def room_on_dirs(P, O, D, F, ring=1):
    """Per unit direction D (an icosphere chart, faces F) the farthest point of P from O binned to it (nan: none),
    dilated by `ring` rings."""
    from scipy.spatial import cKDTree
    Q = P - O
    r = np.linalg.norm(Q, axis=1)
    _, j = cKDTree(D).query(Q / r[:, None])
    R = np.full(len(D), -1.0)
    np.maximum.at(R, j, r)
    R = np.where(R > 0, R, np.nan)
    return ring_max(fill_nan(R, F), F, ring) if ring else R


def convex_rim(table, al, be, bad, pad, rnd, res=0.25):
    """The cop's outline trimmed off the swept room as ONE smooth convex rim (no notch where the room bites): in the
    pole's chart (x, y) = alpha (cos beta, sin beta) (deg) the outline table's region is cut by a half-plane square to
    each bad point's ray `pad` deg inside it (a straight chord, never a notch), then opened by a disk of `rnd` deg (its
    corners rounded). Returns g per point (signed distance to the rim in deg, > 0 inside) and the rim's alpha per
    beta (deg) as a function."""
    from scipy import ndimage
    bg = np.arange(-180.0, 180.0, res)
    lim = interp_table(table, np.abs(bg))
    if bad.any():
        ab, bb = al[bad], np.radians(be[bad])
        for k in range(0, len(ab), 512):
            cs = np.cos(np.radians(bg)[:, None] - bb[None, k:k + 512])
            ch = np.where(cs > 0.05, (ab[None, k:k + 512] - pad) / np.maximum(cs, 0.05), np.inf)
            lim = np.minimum(lim, ch.min(1))
    lim = np.maximum(lim, 0.0)
    R = float(np.max(table, axis=0)[1]) + rnd + 4.0
    n = int(np.ceil(R / res))
    ax = np.arange(-n, n + 1) * res
    X, Y = np.meshgrid(ax, ax, indexing="ij")
    inside = np.hypot(X, Y) < np.interp(np.degrees(np.arctan2(Y, X)), bg, lim, period=360.0)
    if rnd > 0:
        er = ndimage.distance_transform_edt(inside) * res > rnd
        inside = ndimage.distance_transform_edt(~er) * res <= rnd
    sd = (ndimage.distance_transform_edt(inside) - ndimage.distance_transform_edt(~inside)) * res

    def at(x, y):
        return ndimage.map_coordinates(sd, [x / res + n, y / res + n], order=1, mode="nearest")
    g = at(al * np.cos(np.radians(be)), al * np.sin(np.radians(be)))
    rs = np.arange(0.0, R, 0.1)
    B = np.radians(bg)
    S = at((rs[None] * np.cos(B)[:, None]).ravel(), (rs[None] * np.sin(B)[:, None]).ravel()).reshape(len(bg), len(rs))
    i = np.argmax(S <= 0, axis=1)
    i = np.where((S <= 0).any(1), np.maximum(i, 1), len(rs) - 1)
    s0, s1 = S[np.arange(len(bg)), i - 1], S[np.arange(len(bg)), i]
    rim = rs[i - 1] + 0.1 * s0 / np.maximum(s0 - s1, 1e-9)

    def rim_of(b):
        return np.interp(np.asarray(b, float), bg, rim, period=360.0)
    return g, rim_of


def arm_frame(ref, side="l"):
    c = ref.joints[f"upperarm_{side}"]
    a = U(ref.joints[f"lowerarm_{side}"] - c)
    up = np.array([0.0, 1.0, 0.0])
    e = U(up - (up @ a) * a)
    f = U(np.cross(a, e))
    if f[2] < 0:
        f = -f
    return c, a, e, f


def liner(ln, ref, cop_ride, c, lpose, above, mat):
    """The pauldron's liner (16 Nov, pauldron-2 r2): dark leather on her skin under the plates, so any opening between
    them shows leather, never skin. Her idle skin (the plates' design pose) in the cop's ride frame is under a plate
    where its normal meets one within ln.reach; that footprint closed over gaps narrower than 2 ln.close, kept
    ln.bodice_back off the kit bodice (its rest mesh), cut on a smooth edge, laid ln.off out from her rest skin, ln.thick
    deep. It bends with her (the install's follow gives it her own weights); mirrored by the caller."""
    from scipy.spatial import cKDTree
    Pi, Ti, _, _, _, P0 = pose_frame(cop_ride, np.round(c, 4), 0.24, lpose["clip"], lpose.get("frame", 0), rest=True)
    _, first, inv = np.unique(np.round(P0 / 1e-6).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    T = inv.ravel()[Ti]
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 2] != T[:, 0])]
    R0, Rp = P0[first], Pi[first]
    _, n0, _ = ref.closest(R0)
    if (vertex_normals(R0, T) * n0).sum(1).mean() < 0:
        T = T[:, ::-1]
    Np = vertex_normals(Rp, T)
    hits = []
    for Vo, Fo in above:
        t_, _ = raycast(Vo, Fo, Rp + Np * 0.0005, Np.copy(), ln.get("reach", 0.05), chunk=48)
        hits.append(np.isfinite(t_))
    hit = np.any(hits, 0)

    def dist_to(m):
        return cKDTree(R0[m]).query(R0)[0] if m.any() else np.full(len(R0), np.inf)
    dc = ln.get("close", 0.012)
    grown = dist_to(hit) <= dc
    closed = dist_to(~grown) > dc
    g = np.where(closed, dist_to(~closed), -dist_to(closed)) + ln.get("margin", 0.0)
    ins = ln.get("inset")
    if ins:
        # (liner "inset" m, pauldron-2 r4: the openings only: none deeper than inset inside any one plate's shadow (her
        # skin whose normal meets that plate), where the steel always covers her; r3's whole liner came out through
        # the steel there in the leap (58.9 mm), where her skin is the tuck's to hide)
        deep = np.zeros(len(R0), bool)
        for h_ in hits:
            deep |= h_ & (dist_to(~h_) > ins)
        g = np.minimum(g, np.where(deep, -dist_to(~deep), dist_to(deep)))
        print(f"liner inset {ins * 1000:.0f} mm: {int(deep.sum())} deep skin pts dropped", flush=True)
    bp = os.path.join(kb.out_root(), ln.get("bodice", "kit_bodice"), ln.get("bodice", "kit_bodice") + ".glb")
    if os.path.exists(bp):
        G = kb_gl(bp)
        g = np.minimum(g, cKDTree(G).query(R0)[0] - ln.get("bodice_back", 0.010))
    g = smooth_scalar(g, T, ln.get("smooth", 6))
    V, F = kh.clip(R0, T, g)
    V, F = kh.weld(V, F)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    E = np.r_[F[:, [0, 1]], F[:, [1, 2]]]
    _, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(V),) * 2), False)
    cnt = np.bincount(lab[F[:, 0]])
    # (with an inset the openings' liner is a ring and strips: every piece of it over min_tris; else the biggest)
    F = F[cnt[lab[F[:, 0]]] >= ln.get("min_tris", 40)] if ins else F[lab[F[:, 0]] == cnt.argmax()]
    _, nn, _ = ref.closest(V)
    Vin = V + nn * ln.get("off", 0.0023)
    N = vertex_normals(Vin, F)
    N = U(np.where(((N * nn).sum(1) < 0)[:, None], -N, N))
    print(f"liner footprint {int(hit.sum())} of {len(R0)} skin pts, {len(F)} tris", flush=True)
    return kh.shell("liner", mat, Vin, F, N, ln.get("thick", 0.0012))


def kb_gl(path):
    """Every vertex and triangle centre of a src glb (rest), [n, 3]."""
    from heroine_neck import _Gl
    G = _Gl(path)
    out = []
    for nd in G.g["nodes"]:
        if "mesh" in nd:
            for p in G.g["meshes"][nd["mesh"]]["primitives"]:
                X = G.get(p["attributes"]["POSITION"]).astype(float)
                out += [X, X[G.get(p["indices"]).reshape(-1, 3).astype(int)].mean(1)]
    return np.vstack(out)


def pauldrons(cfg, ref):
    gold, steel, leath = cfg["mat"]["trim"], cfg["mat"]["plate"], cfg["mat"]["strap"]
    rim, ck, lk = cfg["rim"], cfg["cop"], cfg["lames"]
    c, a, e, f = arm_frame(ref)

    def ride_of(part):
        # (a rigid group's ride, from params.rigid_ride (match "<part>"): the one place the rides are set, 16 Nov r2:
        # the cop on pauldron_hinge_l (its own helper: clavicle + half the arm's swing), lame0 halfway, lame1 the arm)
        return next((r["weights"] for r in cfg.get("params", {}).get("rigid_ride", []) if r["match"] == part), None)
    # (cop "pole_up" k: the cop's pole tipped from the arm's up-out normal toward world up by k (0..1), and its centre
    # raised by "rise" m: at k 0 the pole stands square to her A-pose arm, the cop sat low and outboard on the deltoid's
    # side; the sheet's cop caps the shoulder's top)
    k_up = ck.get("pole_up", 0.0)
    near = ref.T[(np.linalg.norm(ref.V[ref.T].mean(1) - c, axis=1) < 0.24)]
    body = [(ref.V, near)]
    # (cop "pose" {"clip", "frame"}: the cop designed on her in that frame (the game's idle), in its ride's rest frame
    # (params.rigid_ride "cop_l"): her skin, arm and world up there; built at her A-pose rest, the half-riding cop
    # tipped its back and neck side up off her shoulder in the idle (16 Nov, lead 3's 1:1 look: a fin by her jaw))
    ca, cup, cbody, cc = a, np.array([0.0, 1.0, 0.0]), body, c
    if ck.get("pose"):
        ride = ride_of("cop_l")
        Pp, Tp, cc, ca, cup = pose_frame(ride, np.round(c, 4), 0.24, ck["pose"]["clip"], ck["pose"].get("frame", 0))
        # ("with_rest": her rest skin joined in, the outer of the two: the cop clears her A-pose too)
        cbody = [(Pp, Tp)] + (body if ck["pose"].get("with_rest") else [])
    if ck.get("chart_ref"):
        # (cop "chart_ref" {"a": [x, y, z], "up": [x, y, z]}: the arm direction and up the cop's chart (pole, beta 0, the
        # outline's front) is set from, in its ride's rest frame, in place of her design pose's own (armor-D r7 17 Nov,
        # body B). Her idle arm hangs near up, so the up-out pole is the small part of up across the arm and turns with
        # which way the arm leans: A's idle arm leans back, B's forward, which turned B's chart about 90 deg (beta 90
        # onto her chest: the cop spread over her bust to x -0.06, its two sides welded at her middle and bent with her
        # skin). A's idle axes here put A's outline on the same parts of B's shoulder; the envelope is still her own
        # design-pose skin. Unset = the pose's (A, unchanged))
        ca, cup = U(np.asarray(ck["chart_ref"]["a"], float)), U(np.asarray(ck["chart_ref"]["up"], float))
    e0 = U(cup - (cup @ ca) * ca)
    f0 = U(np.cross(ca, e0))
    f0 = f0 if f0[2] >= 0 else -f0
    ec = U((1 - k_up) * e0 + k_up * cup)
    fc = U(np.cross(ca, ec))
    fc = fc if fc[2] >= 0 else -fc
    # ---- the cop: rays from inside her shoulder round the up-out pole e
    Vs, Fs = icosphere(ck.get("subdiv", 5))
    O = cc - e0 * ck["sink"] + cup * ck.get("rise", 0.0)
    ce, cf = (ec, fc) if k_up else (e0, f0)

    def outline_at(b):
        # (cop "outline_signed": the outline over signed beta -180..180 (+ toward f), in place of the symmetric
        # "outline": built on her idle the chart turns with her arm (beta 0 points up-in-FRONT there, beta 90
        # front-out, -45 the neck side), and the sheet's cop caps the front of her shoulder down to about her arm's
        # joint, which r5's symmetric one left bare (16 Nov, lead 4))
        b = np.asarray(b, float)
        if "outline_signed" in ck:
            return interp_table(ck["outline_signed"], b)
        return interp_table(ck["outline"], np.abs(b))
    alpha = np.degrees(np.arccos(np.clip(Vs @ ce, -1, 1)))
    keep = alpha < ck["chart_deg"]
    if "env_margin" in ck:
        # (the envelope from the directions within the outline + env_margin deg only: rays past the neck-side rim
        # met her neck far out, and the dilation carried that height onto the cop's neck side)
        keep &= alpha < outline_at(np.degrees(np.arctan2(Vs @ cf, Vs @ -ca))) + ck["env_margin"]
    dome = Dome(O, Vs, Fs, keep, cbody, 0.25, ck["dilate"], ck["smooth"], ck["clear"])
    al = np.degrees(np.arccos(np.clip(dome.D @ ce, -1, 1)))
    be = np.degrees(np.arctan2(dome.D @ cf, dome.D @ -ca))
    amax = outline_at(be)
    g = amax - al
    # (the sheet's cop is a round dome whose rim stands well off the arm: "flare" m added toward the rim, as
    # (alpha / alpha_max) ** flare_pow)
    rho = dome.rho + ck.get("flare", 0.0) * np.clip(al / amax, 0, 1) ** ck.get("flare_pow", 2.0)
    cr = ck.get("crown")
    if cr:
        # (cop "crown" {"h": m, "al": deg, "be": deg, "r": deg}: the dome's rise, h on the chart's direction (al, be),
        # falling as cos^2 to 0 at r deg off it: her skin's envelope alone read flat on her shoulder's top, and the
        # sheet's cop is a high round dome over the deltoid's front and top)
        ta, tb = np.radians(cr.get("al", 0.0)), np.radians(cr.get("be", 0.0))
        ax = U(np.cos(ta) * ce + np.sin(ta) * (np.cos(tb) * -ca + np.sin(tb) * cf))
        ang = np.degrees(np.arccos(np.clip(dome.D @ ax, -1, 1)))
        rho = rho + cr["h"] * np.cos(np.clip(ang / cr["r"], 0, 1) * np.pi / 2) ** 2
    sw = cfg.get("sweep")
    room = None
    rim_al = None
    if sw:
        # (rigid by the swept room: her skin over the demo clips carried into the ride's rest frame; the cop stands
        # sw.clear outside it, lifted by at most sw.lift_max (smoothed); where it would need more, the outline is
        # trimmed there: her trapezius under the cop's neck side when the arm is raised)
        # ("cop_ride": the cop's own blend when it does not ride sw.bone as the lames do (its rigid_ride))
        # (sweep "exclude" leaves her torso's skin out of the rows' rooms; "cop_exclude" (default: the same) the cop's)
        croom = sweep_room(sw.get("cop_ride") or ride_of("cop_l") or sw["bone"], np.round(c, 4), sw["radius"],
                           exclude=sw.get("cop_exclude", sw.get("exclude")))
        room = sweep_room(sw["bone"], np.round(c, 4), sw["radius"], exclude=sw.get("exclude")) if "cop_ride" in sw             else croom
        R = room_on_dirs(croom, O, dome.D, dome.F, sw.get("ring", 1))
        need = np.where(np.isfinite(R), R + sw["clear"], 0.0)
        lift = np.clip(need - rho, 0.0, sw.get("cop_lift_max", sw["lift_max"]))
        lift = smooth_scalar(ring_max(lift, dome.F, 2), dome.F, sw.get("lift_smooth", 8))
        rho = rho + lift
        h = smooth_scalar(rho - need, dome.F, sw.get("trim_smooth", 4))
        if sw.get("trim", "contour") == "convex":
            # (one smooth convex rim inside every point the room still bites (h < -trim_tol), plus the rolled rim's
            # half width (trim_pad deg); the contour way below cut a notch along h = 0)
            bad = (h < -sw.get("trim_tol", 0.0)) & (al < amax + sw.get("trim_pad", 2.0))
            g, rim_al = convex_rim(ck["outline"], al, be, bad, sw.get("trim_pad", 2.0), sw.get("trim_round", 6.0))
            ob = np.array([0, 30, 60, 90, 120, 150, 180])
            print("cop trim: bad", int(bad.sum()), "rim alpha at beta", dict(zip(ob.tolist(), np.round(rim_al(ob), 1)
                                                                                .tolist())), flush=True)
        elif sw.get("trim", "contour") == "contour":
            g = np.minimum(g, h * 1000.0 * sw.get("deg_per_mm", 2.0))
        # (the design check: the swept room past the cop's inner face inside its outline, mm: her skin through it)
        R0_ = room_on_dirs(croom, O, dome.D, dome.F, 0)
        bite = np.where(np.isfinite(R0_) & (g > 0), R0_ - rho, -np.inf) * 1000
        print(f"cop room bite max {bite.max():.1f} mm, dirs >2 mm {int((bite > 2).sum())} >0 {int((bite > 0).sum())}",
              flush=True)
    if rim_al is None:
        def rim_al(b):
            return outline_at(b)
    dome.rho = rho
    dome.P = dome.O + dome.D * rho[:, None]
    V, F, N = dome.cut(g)
    print("cop rim loops", len(kh.boundary_loops(F)), "pts", len(V), flush=True)
    th = cfg["thick"]
    cop = kh.shell("cop", steel, V, F, N, th)
    nref = kh.Normals(V + N * th, N)
    G = {"cop": [cop], "cop_gold": [], "lames": [], "lames_gold": [], "strap": []}
    for L in loops_ordered(V + N * (th * 0.5), F):
        G["cop_gold"].append(path_bead("cop_rim", gold, L, nref, rim, 0.0, True))

    def on_cop(al_, be_, lift):
        d = U(np.cos(np.radians(al_))[:, None] * ce + np.sin(np.radians(al_))[:, None] *
              (np.cos(np.radians(be_))[:, None] * -ca + np.sin(np.radians(be_))[:, None] * cf))
        t = cast_union(O, d, [(V + N * th, F)], 0.3)
        ok = np.isfinite(t)
        return O + d[ok] * t[ok, None], d[ok], ok
    # rivets along the (trimmed) rim; "skip" deg: none within that beta of the neck side (the ridge stands there)
    rv = ck["rivets"]
    bb = np.arange(-rv["beta"], rv["beta"] + 1e-6, rv["step"])
    bb = bb[np.abs(bb) >= rv.get("skip", 0.0)]
    pts, d, _ = on_cop(rim_al(bb) - rv["in_deg"], bb, 0)
    for p in pts:
        q, n, _ = nref.closest(p[None])
        G["cop_gold"].append(rivet(p, n[0], r=rv["r"], h=rv["h"], name="cop_rivet", material=gold))
    # the upturned ridge on the neck-side edge, along the (trimmed) rim
    rd = ck["ridge"]
    # (ridge "be0": the beta it centres on; built on her idle the neck side is near beta -45, and beta 0 points
    # up-in-front, where a ridge stood on the dome's face (16 Nov, lead 4))
    b0 = rd.get("be0", 0.0)
    bb = np.linspace(b0 - rd["beta"], b0 + rd["beta"], 41)
    base, d, ok = on_cop(rim_al(bb) - rd["in_deg"], bb, 0)
    bb = bb[ok]
    q, n, _ = nref.closest(base)
    h = rd["h"] * np.sin(np.pi * np.clip((bb - b0 + rd["beta"]) / (2 * rd["beta"]), 0, 1)) ** 0.6
    lean = U(n + (-ca) * rd["lean"])
    top = base + lean * h[:, None]
    if ck.get("pose"):
        # (the design check at the neck side: the ridge and the rim's gap to her idle skin, mm (r3's 1:1 chest: gold and
        # skin interleaved there))
        from native_build import Ref
        hr = Ref(cbody[0][0], cbody[0][1])
        Lr = np.vstack(loops_ordered(V + N * (th * 0.5), F))
        br = np.degrees(np.arctan2((Lr - O) @ cf, (Lr - O) @ -ca))
        for nm_, X_, b_ in (("ridge top", top, bb), ("ridge base", base, bb), ("rim", Lr, br)):
            sel_ = (b_ > -100) & (b_ < 10)
            q_, n_, _ = hr.closest(X_[sel_])
            gp = ((X_[sel_] - q_) * n_).sum(1) * 1000
            print(f"cop {nm_} gap to her idle skin (beta -100..10) mm: min {gp.min():.1f} at beta {b_[sel_][gp.argmin()]:.0f}"
                  f", n<3mm {int((gp < 3).sum())} of {len(gp)}", flush=True)
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
    from scipy.ndimage import grey_dilation
    # (lames "pose" {"clip", "frame"} (16 Nov, pauldron-2): each row designed on her in that frame (the cop's), in its
    # own ride's rest frame (row "ride", default sweep.bone), so the idle shows them as built round her idle arm; a
    # row "tuck" m tucks it that far under the plates above it (the cop, the rows before it) where they cover it, as
    # the sheet's lames sit under the cop and each other with no skin between; the rows' rides step from the cop's
    # toward the arm so they slide over each other as the arm lifts)
    lpose = lk.get("pose")
    cop_ride = next(r["weights"] for r in cfg["params"]["rigid_ride"] if r["match"] == "cop_l")
    if lpose:
        Pc_ = pose_frame(cop_ride, np.round(c, 4), 0.24, lpose["clip"], lpose.get("frame", 0))[0]
    above = [(V, F)]   # plates above the next row, in the cop's ride frame: inner surfaces

    def row_frame(ride):
        """A row's design frame: joint, arm axis, up-out, front, her skin there, and the affine maps cop frame <->
        row frame (the same skin points in both: exact for linear blends)."""
        if not lpose:
            return c, a, e, f, body, None, None
        P_, T_, c_, a_, up_ = pose_frame(ride, np.round(c, 4), 0.24, lpose["clip"], lpose.get("frame", 0))
        # (lames "up_ref" [x, y, z]: as the cop's, the rows' up in their ride's rest frame (theta 0 = up-out); unset =
        # world up carried from the design pose)
        up_ = U(np.asarray(lk["up_ref"], float)) if lk.get("up_ref") else up_
        e_ = U(up_ - (up_ @ a_) * a_)
        f_ = U(np.cross(a_, e_))
        f_ = f_ if f_[2] >= 0 else -f_
        to_row = np.linalg.lstsq(np.c_[Pc_, np.ones(len(Pc_))], P_, rcond=None)[0]
        to_cop = np.linalg.lstsq(np.c_[P_, np.ones(len(P_))], Pc_, rcond=None)[0]
        return c_, a_, e_, f_, [(P_, T_)], to_row, to_cop

    def lame_row(lm, lo, hi, fr, rroom, over):
        """One row over theta lo..hi (deg): its cells' axis points Oa, directions Dd, radius r (her envelope
        dilated, smoothed, + clear + flare; with the swept room: at least sw.clear outside it; tucked under `over`),
        the room's lift."""
        c_, a_, e_, f_, body_ = fr[:5]
        Rn = lm["n"]
        s0, s1 = lm["s"]
        thd = np.linspace(lo, hi, C)
        thr = np.radians(thd)
        rad = np.cos(thr)[:, None] * e_ + np.sin(thr)[:, None] * f_
        dip = lm["dip"] * np.cos(np.radians(thd) * 90.0 / lk["theta"])
        S = np.linspace(0, 1, Rn)[:, None] * (s1 + dip - s0)[None, :] + s0
        Oa = c_[None, None] + S[..., None] * a_
        Dd = np.broadcast_to(rad[None], (Rn, C, 3)).copy()
        t = cast_union(Oa.reshape(-1, 3), Dd.reshape(-1, 3).copy(), body_, 0.2).reshape(Rn, C)
        t = kb.fill_rows(t)
        r = grey_dilation(t, size=(lm["dil"], lm["dil"]))
        r = kb.gsmooth(r, (1.5, 2.0), False)
        r = np.maximum(r, t) + lm["clear"] + lm["flare"] * np.linspace(0, 1, Rn)[:, None] ** 2
        lift = np.zeros(C)
        if rroom is not None:
            # (the row's cells (s, theta) over the swept room, its farthest radius per cell)
            Qr = rroom - c_
            sp_ = Qr @ a_
            rp_ = np.linalg.norm(Qr - sp_[:, None] * a_, axis=1)
            tp_ = np.degrees(np.arctan2(Qr @ f_, Qr @ e_))
            j = np.round((tp_ - lo) / (hi - lo) * (C - 1)).astype(int)
            okj = (j >= 0) & (j < C)
            j = np.clip(j, 0, C - 1)
            i = np.round((sp_ - s0) / np.maximum(S[-1, j] - s0, 1e-6) * (Rn - 1)).astype(int)
            ok = okj & (i >= 0) & (i < Rn) & (rp_ < 0.2)
            Rm = np.full(Rn * C, -1.0)
            np.maximum.at(Rm, i[ok] * C + j[ok], rp_[ok])
            Rm = grey_dilation(Rm.reshape(Rn, C), size=(3, 3))
            need = np.where(Rm > 0, Rm + sw["clear"], 0.0)
            lift = (need - r).max(0)
            r = np.maximum(r, kb.gsmooth(np.maximum(r, need), (1.0, 1.0), False))
            r = np.maximum(r, need)
        ntuck = 0
        if over and lm.get("tuck"):
            # (under the plates above: their nearest inner surface along the cell's ray, less the tuck gap; never
            # nearer her skin than tuck_min)
            tov = np.full(Rn * C, np.inf)
            for Vo, Fo in over:
                to_, _ = raycast(Vo, Fo, Oa.reshape(-1, 3), Dd.reshape(-1, 3).copy(), 0.25, chunk=48)
                tov = np.fmin(tov, np.where(np.isfinite(to_), to_, np.inf))
            tov = tov.reshape(Rn, C) - lm["tuck"]
            hit = np.isfinite(tov) & (tov < r)
            ntuck = int(hit.sum())
            r = np.where(hit, tov, r)
            r = np.where(np.isfinite(tov), np.minimum(kb.gsmooth(r, (1.0, 1.0), False), np.maximum(tov, r)), r)
            r = np.maximum(r, t + lm.get("tuck_min", 0.006))
        bite = -np.inf
        if rroom is not None:
            # (the design check: the swept room past the row's inner face (cells it reaches, undilated), m)
            Rm0 = np.full(Rn * C, -1.0)
            np.maximum.at(Rm0, i[ok] * C + j[ok], rp_[ok])
            Rm0 = Rm0.reshape(Rn, C)
            bite = float(np.where(Rm0 > 0, Rm0 - r, -np.inf).max())
        return Rn, thd, Oa, Dd, r, lift, ntuck, bite

    rows_out = []
    design = []     # (the rows' inner grids in their rides' rest frames: kit_cache/paul_design.npz, for overlap checks)
    for k, lm in enumerate(lk["rows"]):
        ride_k = lm.get("ride") or ride_of(f"lame{k}_l") or {sw["bone"] if sw else "delt_l": 1.0}
        fr = row_frame(ride_k)
        rroom = (sweep_room(ride_k, np.round(c, 4), sw["radius"], exclude=sw.get("exclude")) if sw else None)
        lmax = lm.get("lift_max", sw["lift_max"] if sw else 1.0)
        over = [(np.c_[Vo, np.ones(len(Vo))] @ fr[5], Fo) for Vo, Fo in above] if fr[5] is not None else []
        lo, hi = -lk["theta"], lk["theta"]
        Rn, thd, Oa, Dd, r, lift, ntuck, bite = lame_row(lm, lo, hi, fr, rroom, over)
        # (row "lift_max_front": the front end's (theta > 0) own limit, 16 Nov pauldron-2 r3: row 0 trimmed at 50 deg
        # left the front of her shoulder to the liner)
        lim = np.where(thd > 0, lm.get("lift_max_front", lmax), lmax)
        print(f"lame{k} lift mm by theta: " + " ".join(f"{t_:.0f}:{l_ * 1000:.0f}" for t_, l_ in zip(thd[::3], lift[::3])),
              flush=True)
        if rroom is not None and (lift > lim).any():
            # (trimmed: each end moves in to the last column (from the middle) the room lifts by at most lift_max)
            m = C // 2
            bad = lift > lim
            jl = max([j for j in range(m) if bad[j]], default=-1) + 1
            jh = min([j for j in range(m, C) if bad[j]], default=C) - 1
            lo, hi = thd[jl], thd[jh]
            Rn, thd, Oa, Dd, r, lift, ntuck, bite = lame_row(lm, lo, hi, fr, rroom, over)
        print(f"lame{k} theta {lo:.0f}..{hi:.0f} r {r.min():.3f}..{r.max():.3f} lift max {lift.max() * 1000:.1f} mm"
              f" tucked {ntuck} room bite max {bite * 1000:.1f} mm ride {ride_k}", flush=True)
        Pin = Oa + Dd * r[..., None]
        design.append({"Pin": Pin, "Dd": Dd, "ride": json.dumps(ride_k)})
        if fr[6] is not None:
            above.append((np.c_[Pin.reshape(-1, 3), np.ones(Rn * C)] @ fr[6], grid_tris(Rn, C)))
        lame = kb.slab(f"lame{k}", steel, Pin, Dd.copy(), th)
        gk = [lame]
        Pout = Pin + Dd * (th * 0.5)
        E = np.vstack([Pout[::-1, 0], Pout[-1, 1:], Pout[-2::-1, -1]])
        gk.append(path_bead(f"lame{k}_rim", gold, E, kh.Normals(Pout.reshape(-1, 3), Dd.reshape(-1, 3)), rim, 0.0,
                            False))
        for j in (2, C - 3):
            p = Pin[Rn // 2, j] + Dd[Rn // 2, j] * (th + 0.0003)
            gk.append(rivet(p, Dd[Rn // 2, j], r=lk["rivet_r"], h=lk["rivet_h"], name="lame_rivet", material=gold))
        rows_out.append((k, gk, Pin, Dd, fr))
        if not lk.get("split"):
            G["lames"].append(lame)
            G["lames_gold"] += gk[1:]
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
    bk = buckle(pb, Dd[2, jb], a, w=sk["w"] * 1.25, h=sk["w"] * 1.0, bar=0.0024, name="strap_buckle", material=gold)
    nodes = {"pauldron_cop_l_rigid": G["cop"] + G["cop_gold"]}
    if lk.get("split"):
        # (one rigid node a row: "pauldron_lame<k>_l_rigid", its own ride (params.rigid_ride match "lame<k>_l"); the
        # strap's buckle rides with the strap's row (the last))
        for k, gk, _, _, _ in rows_out:
            nodes[f"pauldron_lame{k}_l_rigid"] = gk + ([bk] if k == len(rows_out) - 1 else [])
    else:
        nodes["pauldron_lames_l_rigid"] = G["lames"] + G["lames_gold"] + [bk]
    nodes["pauldron_strap_l"] = G["strap"]
    lnr = cfg.get("liner")
    if lnr and lpose:
        nodes["pauldron_liner_l"] = [liner(lnr, ref, cop_ride, c, lpose, above, leath)]
    if lpose:
        os.makedirs(kb.CACHE, exist_ok=True)
        np.savez_compressed(os.path.join(kb.CACHE, "paul_design.npz"), cop_V=V, cop_F=F, cop_N=N, thick=th, cop_O=O,
                            cop_ride=json.dumps(cop_ride), **{f"row{k}_{nm}": d[nm] for k, d in enumerate(design)
                                                             for nm in ("Pin", "Dd", "ride")})
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
    cfg = cfg or json.load(open(os.path.join(kb.SRC, pid, "build.json"), encoding="utf-8"))
    d = kb.out_dir(pid)
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
             "params": {"file": f"{pid}.glb", **cfg.get("params", {})},
             **{k: v for k, v in piece.items() if k not in ("id", "name", "slot")},
             "layer": cfg["piece"].get("layer", 1), "body_sha1": hashlib.sha1(open(kb.body_glb(), "rb").read()).hexdigest()}
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
    import bodies
    bodies.take(sys.argv)
    build(sys.argv[1])
