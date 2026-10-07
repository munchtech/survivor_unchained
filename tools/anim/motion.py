"""Motion measured on her actual body, clip by clip: what the owner sees.

    python tools/anim/motion.py [names...] [--hero] [--outfits] [--save NAME] [--against NAME]

For every frame of a clip (her springs running, as in the game), it measures:

- **contact**: how deep each arm goes into the rest of her (her trunk and
  breasts, her legs, her head, the other arm), on her skin, and with each
  outfit's thickness laid on (an arm in a bracer against a plate cup meets
  it sooner). Depths are in millimetres; the armpit, where skin is meant to
  fold, is kept apart;
- **volume**: how much of the flesh round each elbow, wrist and knee is kept
  as it bends and turns (the region from 8 cm up the bone above to 8 cm
  down the one below, as a share of its volume at rest). Linear skinning
  loses it: a pinched elbow, a wrist wrung like a sweet wrapper;
- **wrist**: the bend toward the palm and back, to the thumb and the little
  finger (on the wrist's own axes), against what a wrist does; and how far
  the forearm bone itself rolls on the elbow (it should not: the radius
  rolls over the ulna below the elbow, and the elbow is a hinge);
- **slide**: how far a foot moves while it is on the ground (cm a step, in
  the world, at the clip's own speed);
- **overlap**: whether the arm moves as one stiff piece or each joint
  follows the one above (how many frames the hand's turn lags the upper
  arm's, at the moments the arm stops or turns back).

`--save NAME` keeps the numbers (out/motion_NAME.json); `--against NAME`
prints them beside an earlier run's.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rig import qinv, qmul, qrot  # noqa: E402
import skin  # noqa: E402
from skin import OUT, Body, Gltf  # noqa: E402
import audit  # noqa: E402

OUTFITS = ("warden", "arcanist", "reaver", "ranger")


# ------------------------------------------------------------ geometry --
def closest_on_tris(p, a, b, c):
    """Closest points on triangles (a, b, c) to points p, all [N, 3], and
    their barycentric weights (Ericson, Real-Time Collision Detection 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    n = len(p)
    u = np.zeros(n)
    v = np.zeros(n)
    w = np.zeros(n)
    done = np.zeros(n, bool)

    def put(m, uu, vv, ww):
        nonlocal done
        m = m & ~done
        u[m], v[m], w[m] = uu[m] if np.ndim(uu) else uu, vv[m] if np.ndim(vv) else vv, ww[m] if np.ndim(ww) else ww
        done |= m

    one, zero = np.ones(n), np.zeros(n)
    put((d1 <= 0) & (d2 <= 0), one, zero, zero)
    put((d3 >= 0) & (d4 <= d3), zero, one, zero)
    put((d6 >= 0) & (d5 <= d6), zero, zero, one)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), 1 - t, t, zero)
        t = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), 1 - t, zero, t)
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), zero, 1 - t, t)
        den = 1 / (va + vb + vc)
        vv, ww = vb * den, vc * den
        put(np.ones(n, bool), 1 - vv - ww, vv, ww)
    q = a * u[:, None] + b * v[:, None] + c * w[:, None]
    return q, np.stack([u, v, w], 1)


def vertex_normals(P, T, n):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros((n, 3))
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


class Surface:
    """A set of her triangles to measure points against: signed distance
    (+ outside, along her skin's normal) to the nearest of them."""

    def __init__(self, T, nverts):
        self.T = T
        self.used = np.unique(T)
        rows = np.repeat(np.arange(len(T)), 3)
        self.v2t = sparse.csr_matrix((np.ones(len(rows)), (T.ravel(), rows)), shape=(nverts, len(T)))
        self.nverts = nverts

    def signed(self, P, Q, reach=0.08, k=12):
        """For points Q against the surface posed at P: (signed distance,
        nearest vertex of the surface) for each point within `reach`, else nan.
        The sign is the nearest feature's (a face's normal inside it, the two
        faces' on an edge, the corner's own at a corner); a point found inside
        by more than 4 mm is confirmed by its winding number among the faces
        round it (a sign read off a thin part's far side is put right)."""
        out = np.full(len(Q), np.nan)
        near = np.full(len(Q), -1)
        tree = cKDTree(P[self.used])
        d, ix = tree.query(Q, k=k, distance_upper_bound=reach)
        hit = np.isfinite(d[:, 0])
        if not hit.any():
            return out, near
        qi = np.nonzero(hit)[0]
        verts = self.used[np.where(np.isfinite(d[hit]), ix[hit], ix[hit][:, :1])]
        # Candidate triangles: those round the nearest vertices.
        sub = self.v2t[verts.ravel()].tocoo()
        rowq = np.repeat(np.arange(len(qi)), k)[sub.row]
        pairs = np.unique(np.stack([rowq, sub.col], 1), axis=0)
        cand_rows, cand_tris = pairs[:, 0], pairs[:, 1]
        tri = self.T[cand_tris]
        p = Q[qi[cand_rows]]
        c, bary = closest_on_tris(p, P[tri[:, 0]], P[tri[:, 1]], P[tri[:, 2]])
        dist = np.linalg.norm(p - c, axis=1)
        # The nearest triangle for each point.
        order = np.lexsort((dist, cand_rows))
        first = np.ones(len(order), bool)
        first[1:] = cand_rows[order][1:] != cand_rows[order][:-1]
        best = order[first]
        bt = tri[best]
        bb = bary[best]
        # The nearest feature's normal: the face's when inside it.
        fn = self.face_n[cand_tris[best]]
        nb = fn.copy()
        onv = (bb > 0.999).any(1)
        nb[onv] = self.normals[bt[onv][np.arange(onv.sum()), bb[onv].argmax(1)]]
        one = (bb < 1e-6).sum(1) == 1
        edge = one & ~onv
        if edge.any():
            # On an edge: its two faces' normals together (the other face
            # found among the candidates that share the edge's corners).
            k0 = bb[edge].argmin(1)
            ea = bt[edge][np.arange(edge.sum()), (k0 + 1) % 3]
            eb = bt[edge][np.arange(edge.sum()), (k0 + 2) % 3]
            nb[edge] = self.normals[ea] + self.normals[eb]
        sgn = np.sign(((p[best] - c[best]) * nb).sum(1))
        sgn[sgn == 0] = 1
        res = dist[best] * sgn
        rows = qi[cand_rows[best]]
        deep = np.nonzero(res < -0.004)[0]
        if len(deep):
            w = self.winding(P, Q[rows[deep]])
            res[deep[w < 0.5]] *= -1
        out[rows] = res
        near[rows] = bt[np.arange(len(best)), bb.argmax(1)]
        return out, near

    def winding(self, P, Q, radius=0.25):
        """Generalised winding numbers of points Q among the faces within
        `radius` of each (about 1 inside her, 0 outside)."""
        A, B, C = P[self.T[:, 0]], P[self.T[:, 1]], P[self.T[:, 2]]
        cen = (A + B + C) / 3
        out = np.zeros(len(Q))
        tree = cKDTree(cen)
        for i, q in enumerate(Q):
            ids = tree.query_ball_point(q, radius)
            if not ids:
                continue
            a, b, c = A[ids] - q, B[ids] - q, C[ids] - q
            la, lb, lc = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1), np.linalg.norm(c, axis=1)
            det = np.einsum("ij,ij->i", a, np.cross(b, c))
            den = la * lb * lc + (a * b).sum(1) * lc + (b * c).sum(1) * la + (c * a).sum(1) * lb
            out[i] = np.arctan2(det, den).sum() / (2 * np.pi)
        return out

    def pose(self, P):
        fn = np.cross(P[self.T[:, 1]] - P[self.T[:, 0]], P[self.T[:, 2]] - P[self.T[:, 0]])
        self.face_n = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        self.normals = vertex_normals(P, self.T, self.nverts)


# --------------------------------------------------------------- her body --
class Measure:
    """The checks for one body (and its outfits' thickness)."""

    def __init__(self, body: Body, outfits=()):
        self.b = body
        b = body
        sk = b.sk
        I = sk.index
        skin = np.nonzero(b.kind == "skin")[0]
        self.skin = skin
        n = len(b.P)
        Tskin = b.T[np.isin(b.T[:, 0], skin)]
        self.Tskin = Tskin
        self.rest_normals = vertex_normals(b.P, Tskin, n)
        # Breast flesh: where a breast bone carries a fifth of a point's weight.
        wb = np.zeros(n)
        for s in "lr":
            j = I.get(f"breast_{s}")
            if j is not None:
                wb += (b.W * (b.J == j)).sum(1)
        self.breast = wb > 0.2
        # Each arm's points, where along the arm they lie (0 at the shoulder,
        # 1 at the elbow, 2 at the wrist, 3 at the knuckles).
        rg, rp = sk.rest_globals()
        rp = rp[0]
        self.arm = {}
        for s in "lr":
            k = b.parts.index("arm_" + s)
            pts = skin[(b.part[skin] == k) & (b.share[skin, k] > 0.95)]
            sh, el, wr, kn = rp[I[f"upperarm_{s}"]], rp[I[f"lowerarm_{s}"]], rp[I[f"hand_{s}"]], rp[I[f"middle_01_{s}"]]
            along = np.zeros(len(pts))
            P = b.P[pts]
            for i0, (a0, a1) in enumerate(((sh, el), (el, wr), (wr, kn))):
                d = a1 - a0
                t = ((P - a0) @ d) / (d @ d)
                seg = np.clip(t, 0, 1)
                dist = np.linalg.norm(P - (a0 + seg[:, None] * d), axis=1)
                if i0 == 0:
                    best, along = dist, i0 + seg
                else:
                    m = dist < best
                    best = np.where(m, dist, best)
                    along = np.where(m, i0 + seg, along)
            self.arm[s] = (pts, along)
            # Everything that is not this arm (nor its shoulder's blend).
            far = b.share[:, k] < 0.05
            T = Tskin[far[Tskin].all(1)]
            self.arm[s] = (pts, along, Surface(T, n))
        # Garments: how far each outfit stands off her skin at each point
        # (laid on her skin's nearest point, along its normal).
        self.cover = {}
        for o in outfits:
            self.cover[o] = self._cover(o)

    def _cover(self, outfit):
        b = self.b
        g = Body(b.sk, [(skin.PEOPLE / f"heroine_outfit_{outfit}.gltf", lambda n, o=outfit: n.startswith(o + "."), "garment")], None)
        skinP = b.P[self.skin]
        tree = cKDTree(skinP)
        gp = g.P[:: max(1, len(g.P) // 150000)]
        d, ix = tree.query(gp, k=1, distance_upper_bound=0.12)
        ok = np.isfinite(d)
        h = ((gp[ok] - skinP[ix[ok]]) * self.rest_normals[self.skin][ix[ok]]).sum(1)
        cov = np.zeros(len(b.P))
        np.maximum.at(cov, self.skin[ix[ok]], np.clip(h, 0, 0.12))
        # Spread to the neighbours a garment point fell between.
        sm = cov.copy()
        T = self.Tskin
        for _ in range(2):
            nb = np.zeros_like(sm)
            for k in range(3):
                np.maximum.at(nb, T[:, k], np.maximum(sm[T[:, (k + 1) % 3]], sm[T[:, (k + 2) % 3]]))
            sm = np.maximum(sm, nb * 0.9)
        return sm

    # ------------------------------------------------------------ contact --
    def contact(self, P):
        """Each arm's points against the rest of her, for posed points P:
        {side: (depth mm [points], along [points], hit part [points], breast hit [points], nearest [points])}."""
        b = self.b
        out = {}
        for s in "lr":
            pts, along, surf = self.arm[s]
            surf.pose(P)
            dist, near = surf.signed(P, P[pts])
            hit = np.where(near >= 0, b.part[np.maximum(near, 0)], -1)
            brst = np.where(near >= 0, self.breast[np.maximum(near, 0)], False)
            out[s] = (dist, along, hit, brst, near)
        return out

    # ------------------------------------------------------------- volume --
    JOINTS = (("elbow", "upperarm", "lowerarm", "hand", 0.08, 0.08),
              ("wrist", "lowerarm", "hand", "middle_01", 0.06, 0.05),
              ("knee", "thigh", "calf", "foot", 0.10, 0.10))

    def regions(self):
        """Each joint's region of her skin at rest: the triangles between a
        plane across the bone above (so far up it) and one across the bone
        below (so far down it), on that limb."""
        if hasattr(self, "_regions"):
            return self._regions
        b = self.b
        sk = b.sk
        I = sk.index
        _, rp = sk.rest_globals()
        rp = rp[0]
        reg = {}
        for name, top, mid, end, up, down in self.JOINTS:
            for s in "lr":
                a, j, e = rp[I[f"{top}_{s}"]], rp[I[f"{mid}_{s}"]], rp[I[f"{end}_{s}"]]
                u = (j - a) / np.linalg.norm(j - a)
                f = (e - j) / np.linalg.norm(e - j)
                part = b.parts.index(("arm_" if name != "knee" else "leg_") + s)
                P = b.P
                ok = (((P - (j - u * up)) @ u) > 0) & (((P - (j + f * down)) @ f) < 0) & (b.share[:, part] > 0.5)
                ok &= np.linalg.norm(np.cross(P - j, u), axis=1) < 0.12
                T = self.Tskin[ok[self.Tskin].all(1)]
                reg[(name, s)] = (T, I[f"{mid}_{s}"])
        self._regions = reg
        return reg

    def volumes(self, P, G):
        out = {}
        for key, (T, j) in self.regions().items():
            o = G[j][:3, 3]
            a, bb, c = P[T[:, 0]] - o, P[T[:, 1]] - o, P[T[:, 2]] - o
            out[key] = float(np.einsum("ij,ij->i", a, np.cross(bb, c)).sum() / 6)
        return out


# ----------------------------------------------------------------- wrists --
def wrist_rows(clip, sk):
    """Per frame and side: (flexion, deviation, hand twist on the forearm,
    forearm roll on the elbow) in degrees."""
    I = sk.index
    rot = clip.rot
    rows = {}
    for s in "lr":
        ua, la, h, mid = I[f"upperarm_{s}"], I[f"lowerarm_{s}"], I[f"hand_{s}"], I[f"middle_01_{s}"]
        fa_axis = sk.rest_pos[h] / np.linalg.norm(sk.rest_pos[h])
        h_axis = sk.rest_pos[mid] / np.linalg.norm(sk.rest_pos[mid])
        r = []
        for f in range(clip.frames):
            dfa = qmul(qinv(sk.rest_rot[la]), rot[f, la])
            dh = qmul(qinv(sk.rest_rot[h]), rot[f, h])
            _, fa_tw = audit.swing_twist(dfa, fa_axis)
            _, h_tw = audit.swing_twist(dh, h_axis)
            flex, dev = audit.wrist_bend(dh, h_axis, s)
            r.append((flex, dev, h_tw, fa_tw))
        rows[s] = np.array(r)
    return rows


# ------------------------------------------------------------------ feet --
def soles(body: Body):
    """Her soles: skin points within 2.5 cm of the ground at rest, by foot."""
    b = body
    sk = b.sk
    out = {}
    skin = b.kind == "skin"
    ground = b.P[skin, 1].min()
    for s in "lr":
        k = b.parts.index("leg_" + s)
        m = skin & (b.part == k) & (b.P[:, 1] < ground + 0.025)
        out[s] = np.nonzero(m)[0]
    return out, ground


def slide(body: Body, clip, Gs, sole, ground):
    """Each foot's planted spells and how far it slid in each (cm, world):
    a sole point on the ground (within 1 cm) that moves along it."""
    res = {}
    for s, idx in sole.items():
        W = []
        for f, G in enumerate(Gs):
            p = body.pose(G, idx)
            wm = body.world(clip, f)
            W.append((wm[:3, :3] @ p.T).T + wm[:3, 3])
        W = np.array(W)                        # [T, n, 3]
        g = ground * body.world_scale
        on = W[:, :, 1] < g + 0.01
        worst = []
        T = len(W)
        # A spell: frames where the lowest point is down.
        down = on.any(1)
        f = 0
        while f < T:
            if not down[f]:
                f += 1
                continue
            e = f
            while e + 1 < T and down[e + 1]:
                e += 1
            # Within the spell, each point's travel while it stays down.
            best = 0.0
            for i in range(W.shape[1]):
                col = on[f:e + 1, i]
                if col.sum() < 2:
                    continue
                k0 = None
                for k in range(f, e + 2):
                    inside = k <= e and on[k, i]
                    if inside and k0 is None:
                        k0 = k
                    if not inside and k0 is not None:
                        if k - 1 > k0:
                            d = np.linalg.norm(W[k0:k, i, [0, 2]] - W[k0, i, [0, 2]], axis=1).max()
                            best = max(best, d)
                        k0 = None
            worst.append((f, e, round(100 * best, 1)))
            f = e + 1
        res[s] = worst
    return res


# --------------------------------------------------------------- overlap --
def overlap(body: Body, clip):
    """For each arm: at each moment the upper arm stops or turns back (its
    turn speed falls through a fifth of its peak), how many frames later
    the hand's own turn (on the forearm) does the same; and how often the
    arm's three joints all stop on the same frame."""
    sk = body.sk
    I = sk.index
    grot, _ = sk.fk(clip.rot, clip.pos)
    out = {}
    for s in "lr":
        def speed(j, rel=None):
            g = grot[:, j] if rel is None else qmul(qinv(grot[:, rel]), grot[:, j])
            d = np.abs((g[1:] * g[:-1]).sum(-1))
            return np.degrees(2 * np.arccos(np.clip(d, 0, 1)))
        su = speed(I[f"upperarm_{s}"], I[f"clavicle_{s}"])
        sf = speed(I[f"lowerarm_{s}"], I[f"upperarm_{s}"])
        sh = speed(I[f"hand_{s}"], I[f"lowerarm_{s}"])
        lags = []
        if su.max() > 2:
            thr = 0.2 * su.max()
            for t in range(1, len(su)):
                if su[t - 1] > thr >= su[t]:
                    # The hand settles later (lags) if it is still turning.
                    k = t
                    while k < len(sh) and sh[k] > 0.2 * max(sh.max(), 1e-6) and k - t < 10:
                        k += 1
                    lags.append(k - t)
        out[s] = {"lags": lags, "peak_upper": float(su.max()), "peak_hand": float(sh.max())}
    return out


# ------------------------------------------------------------------ main --
def run_clip(m: Measure, mw: Measure | None, name, outfits):
    b = m.b
    clip = b.clip(name)
    res = {"frames": clip.frames, "loop": clip.loop}
    # Two runs of the springs: plate holds her (warden), the rest swing free.
    sets = [("free", m)]
    if mw is not None and "warden" in outfits:
        sets.append(("plate", mw))
    for tag, mm in sets:
        bb = mm.b
        Gs = bb.frames(clip)
        depth = {s: [] for s in "lr"}
        vols = []
        for f, G in enumerate(Gs):
            P = bb.pose(G)
            con = mm.contact(P)
            for s in "lr":
                dist, along, hit, brst, near = con[s]
                depth[s].append((dist, hit, brst, near))
            if tag == "free":
                vols.append(mm.volumes(P, G))
        res[tag] = depth
        if tag == "free":
            rest = m.volumes(b.P, b.rest)
            res["volume"] = {f"{k[0]}_{k[1]}": [v[k] / rest[k] for v in vols] for k in rest}
    res["wrist"] = wrist_rows(clip, b.sk)
    sole, ground = soles(b)
    res["slide"] = slide(b, clip, b.frames(clip), sole, ground)
    res["overlap"] = overlap(b, clip)
    return res


def summarise(m: Measure, res, outfits):
    """The numbers that matter, per clip."""
    b = m.b
    out = {}
    parts = b.parts
    for s in "lr":
        pts, along, _ = m.arm[s]
        for cov_name in ("skin",) + tuple(outfits):
            tag = "plate" if cov_name == "warden" and "plate" in res else "free"
            worst = {"armpit": 0.0, "upper": 0.0, "forearm": 0.0, "hand": 0.0}
            where = {}
            breast = 0.0
            frames_bad = 0
            for f, (dist, hit, brst, near) in enumerate(res[tag][s]):
                ok = np.isfinite(dist)
                if not ok.any():
                    continue
                d = -dist.copy()
                if cov_name != "skin":
                    cov = m.cover[cov_name]
                    d[ok] += cov[pts[ok]] + cov[np.maximum(near[ok], 0)]
                d[~ok] = -1
                zone = np.where(along < 0.35, 0, np.where(along < 1, 1, np.where(along < 2, 2, 3)))
                bad = False
                for zi, zn in enumerate(("armpit", "upper", "forearm", "hand")):
                    mk = (zone == zi) & ok
                    if mk.any():
                        dz = float(d[mk].max())
                        if dz > worst[zn]:
                            worst[zn] = dz
                            i = np.nonzero(mk)[0][d[mk].argmax()]
                            where[zn] = (f, parts[hit[i]] if hit[i] >= 0 else "-", bool(brst[i]))
                        if zi > 0 and dz > 0.005:
                            bad = True
                mb = ok & brst
                if mb.any():
                    breast = max(breast, float(d[mb].max()))
                frames_bad += bad
            out[f"contact_{s}_{cov_name}"] = {k: round(1000 * max(v, 0), 1) for k, v in worst.items()}
            out[f"contact_{s}_{cov_name}"]["breast"] = round(1000 * max(breast, 0), 1)
            out[f"contact_{s}_{cov_name}"]["frames"] = frames_bad
            out[f"contact_{s}_{cov_name}"]["at"] = where
    out["volume"] = {k: round(100 * min(v), 1) for k, v in res["volume"].items()}
    w = res["wrist"]
    out["wrist"] = {s: {"flex": round(float(w[s][:, 0].max()), 0), "ext": round(float(-w[s][:, 0].min()), 0),
                        "radial": round(float(w[s][:, 1].max()), 0), "ulnar": round(float(-w[s][:, 1].min()), 0),
                        "hand_twist": round(float(np.abs(w[s][:, 2]).max()), 0),
                        "forearm_roll": round(float(np.abs(w[s][:, 3]).max()), 0),
                        "bend_step": round(float(np.abs(np.diff(w[s][:, :2], axis=0)).max()) if len(w[s]) > 1 else 0, 0)}
                    for s in "lr"}
    out["slide"] = {s: max([x[2] for x in v], default=0.0) for s, v in res["slide"].items()}
    out["overlap"] = {s: v["lags"] for s, v in res["overlap"].items()}
    return out


def clip_names(folder, want):
    names = sorted(p.stem for p in folder.glob("*.json"))
    return [n for n in names if not want or any(w == n or (w.endswith("*") and n.startswith(w[:-1])) for w in want)]


def main(argv):
    want = [a for a in argv if not a.startswith("--") and not a.endswith(".json")]
    hero = "--hero" in argv
    save = argv[argv.index("--save") + 1] if "--save" in argv else None
    if save in want:
        want.remove(save)
    outfits = OUTFITS if ("--outfits" in argv and not hero) else ()
    t0 = time.time()
    if hero:
        m = Measure(Body.hero())
        mw = None
        folder = OUT / "hero"
    else:
        m = Measure(Body.heroine(jiggle=True), outfits)
        mw = Measure(Body.heroine(outfit=None, jiggle=True), ()) if outfits else None
        if mw is not None:
            mw.b.jiggle.amount, mw.b.jiggle.squash = 0.55, 0.0
            mw.cover = m.cover
        folder = OUT / "clips"
    print(f"(body ready in {time.time() - t0:.1f} s)")
    names = clip_names(folder, want)
    results = {}
    for n in names:
        t1 = time.time()
        res = run_clip(m, mw, n, outfits)
        s = summarise(m, res, outfits)
        results[n] = s
        print(line(n, s, outfits), f"({time.time() - t1:.1f} s)")
    if save:
        p = OUT / f"motion_{save}{'_hero' if hero else ''}.json"
        p.write_text(json.dumps(results, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
        print("saved", p)


def line(n, s, outfits):
    c = []
    for side in "lr":
        k = s[f"contact_{side}_skin"]
        c.append(f"{side}: up {k['upper']:4.0f} fa {k['forearm']:4.0f} hd {k['hand']:4.0f} br {k['breast']:4.0f} pit {k['armpit']:3.0f}")
        for o in outfits:
            ko = s[f"contact_{side}_{o}"]
            c.append(f"{o[:3]} {max(ko['upper'], ko['forearm'], ko['hand']):3.0f}")
    v = s["volume"]
    vol = f"vol el {v['elbow_l']:.0f}/{v['elbow_r']:.0f} wr {v['wrist_l']:.0f}/{v['wrist_r']:.0f} kn {v['knee_l']:.0f}/{v['knee_r']:.0f}"
    w = s["wrist"]
    wr = " ".join(f"{sd}:f{w[sd]['flex']:.0f}/e{w[sd]['ext']:.0f}/r{w[sd]['radial']:.0f}/u{w[sd]['ulnar']:.0f}/roll{w[sd]['forearm_roll']:.0f}" for sd in "lr")
    sl = f"slide {s['slide']['l']:.1f}/{s['slide']['r']:.1f}"
    return f"{n:24s} | {' '.join(c)} | {vol} | {wr} | {sl}"


if __name__ == "__main__":
    main(sys.argv[1:])
