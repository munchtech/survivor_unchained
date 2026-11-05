"""Joint-bend strips: elbow and knee flexion, shoulder abduction and flexion, hip flexion, at 0 (rest), 90 and 135
degrees, both sides, posed through a poser (posers.py) and measured in the limb's own frame.

Nothing assumes her skeleton: bones come by role (ROLES, rig.json "roles" overrides), the body's frame (up, her
left, her front) from the shoulder and hip heads, each motion's axis from the bones' rest directions:
  Every strip angle is ABSOLUTE and anatomical, measured from the posed bone directions (0 = the rest pose as built,
  with each body's own rest angle printed as rest_angle_deg), so bodies with different rest poses compare like for like:
  elbow / knee flexion:  the angle between the proximal and distal bones (0 = straight); the turn is about the hinge
                         (across the proximal bone and her front; rig.json "hinge": {"elbow": "plane"} uses the normal
                         of the upper/lower bone plane at rest, "local_x" the bone's own rest X), solved for the angle;
  shoulder abduction:    the upper arm's angle from the torso's down axis in the frontal plane (0 = hanging, 90 = out
                         horizontal), turned about her front; the forearm keeps its rest flexion;
  shoulder flexion:      the same forward in the sagittal plane (90 = forward horizontal), turned about her left-right axis;
  hip flexion:           the thigh's angle from the down axis, forward in the sagittal plane (0 = standing).
  Each turn is solved (bisection) for the target; check.json carries target_deg and achieved_deg per strip angle.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull, cKDTree

import ray

HERE = Path(__file__).resolve().parent
ROLES = {"upperarm": "upperarm_{s}", "lowerarm": "lowerarm_{s}", "hand": "hand_{s}",
         "thigh": "thigh_{s}", "calf": "calf_{s}", "foot": "foot_{s}"}
ALIASES = {"upperarm": ["upper_arm.{S}", "UpperArm_{S}", "upperarm.{S}", "upperarm01_{s}", "upperarm01.{S}"],
           "lowerarm": ["forearm.{S}", "lowerarm01_{s}", "lowerarm01.{S}", "ForeArm_{S}"],
           "hand": ["hand.{S}", "wrist_{s}", "wrist.{S}", "Hand_{S}"],
           "thigh": ["thigh.{S}", "upperleg01_{s}", "upperleg01.{S}", "UpLeg_{S}"],
           "calf": ["shin.{S}", "lowerleg01_{s}", "lowerleg01.{S}", "Leg_{S}"],
           "foot": ["foot.{S}", "Foot_{S}"]}
ANGLES = (0, 90, 135)
# measured but not drawn (the sheet keeps its three panels): the hip's in-between, where the D verdict asks the
# corrective to hold between 90 and 135 (fix 1: "an in-between at about 112")
EXTRA = {"hip_flex": (112,)}
PX_CLOSE = 940.0        # px per metre at the close-up (9.4 px/cm)
MOTIONS = {
    #               bone        proximal    distal end  stations (seg, s of that segment's length)
    "elbow":        ("lowerarm", "upperarm", "hand", [("p", 0.5), ("p", 0.25), ("p", 0.1), ("d", 0.1), ("d", 0.25)]),
    "knee":         ("calf", "thigh", "foot", [("p", 0.5), ("p", 0.25), ("p", 0.1), ("d", 0.1), ("d", 0.25)]),
    "shoulder_abd": ("upperarm", None, "lowerarm", [("d", 0.25), ("d", 0.4), ("d", 0.55), ("d", 0.75)]),
    "shoulder_flex": ("upperarm", None, "lowerarm", [("d", 0.25), ("d", 0.4), ("d", 0.55), ("d", 0.75)]),
    "hip_flex":     ("thigh", None, "calf", [("d", 0.25), ("d", 0.4), ("d", 0.55), ("d", 0.75)]),
}
NEAR_M = {"elbow": 0.08, "knee": 0.10, "shoulder_abd": 0.12, "shoulder_flex": 0.12, "hip_flex": 0.14}


def unit(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-12)


def perp(v, n):
    return unit(v - n * (v @ n))


def rot(axis, deg):
    a = unit(axis)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def _ang3(a, b):
    return math.degrees(math.acos(float(np.clip(unit(a) @ unit(b), -1, 1))))


def bone(poser, rig, role, s):
    roles = {**ROLES, **rig.get("roles", {})}
    for cand in [roles[role]] + ALIASES.get(role, []):
        nm = cand.replace("{s}", s).replace("{S}", s.upper())
        if nm in poser.index:
            return nm
    raise KeyError(f"no bone for role {role} side {s} (set rig.json roles)")


class Frame:
    """Her body's frame from the skeleton at rest: up (hips to shoulders), lat (toward her left), front."""

    def __init__(self, poser, rig):
        h = lambda r, s: poser.rest[poser.index[bone(poser, rig, r, s)]][:3, 3]
        sh = (h("upperarm", "l") + h("upperarm", "r")) / 2
        hip = (h("thigh", "l") + h("thigh", "r")) / 2
        self.up = unit(sh - hip)
        self.lat = perp(h("upperarm", "l") - h("upperarm", "r"), self.up)
        self.front = np.cross(self.lat, self.up)
        self.center = (sh + hip) / 2


class Strip:
    """One motion on one side: its pose at each angle and its view."""

    def __init__(self, poser, rig, frame, motion, s):
        self.poser, self.rig, self.fr, self.motion, self.s = poser, rig, frame, motion, s
        bn, prox, end, self.stations = MOTIONS[motion]
        I = poser.index
        self.bone = bone(poser, rig, bn, s)
        self.end = bone(poser, rig, end, s)
        self.j, self.je = I[self.bone], I[self.end]
        R = poser.rest
        self.O = R[self.j][:3, 3].copy()
        self.Ld = float(np.linalg.norm(R[self.je][:3, 3] - self.O))
        out = frame.lat * (1 if s == "l" else -1)
        up, front = frame.up, frame.front
        u_d = unit(R[self.je][:3, 3] - self.O)
        hinge = rig.get("hinge", {}).get(motion, "front")
        if motion in ("elbow", "knee"):
            self.prox = bone(poser, rig, prox, s)
            jp = I[self.prox]
            u = unit(self.O - R[jp][:3, 3])
            self.Lp = float(np.linalg.norm(self.O - R[jp][:3, 3]))
            self.p3 = -u
            self.u_prox = u
            self.b = perp(front if motion == "elbow" else -front, u)
            a = np.cross(u, self.b)
            if hinge == "plane":
                a2 = np.cross(u, u_d)
                if np.linalg.norm(a2) > 0.05:
                    a = unit(a2) * np.sign(unit(a2) @ a)
            elif hinge == "local_x":
                x = unit(R[self.j][:3, 0])
                a = x * np.sign(x @ a)
            self.axis = unit(a)
            self.meas = lambda d, u=u: _ang3(u, d)
        elif motion == "shoulder_abd":
            self.prox, self.Lp = None, self.Ld
            self.p3 = -up
            self.b = out
            self.axis = unit(np.cross(out, up))
            self.meas = lambda d: math.degrees(math.atan2(d @ out, -(d @ up)))
        elif motion == "shoulder_flex":
            self.prox, self.Lp = None, self.Ld
            self.p3 = -up
            self.b = front
            self.axis = unit(np.cross(front, up))
            self.meas = lambda d: math.degrees(math.atan2(d @ front, -(d @ up)))
        else:   # hip_flex
            self.prox, self.Lp = None, self.Ld
            self.p3 = up
            self.b = front
            self.axis = unit(np.cross(front, up))
            self.meas = lambda d: math.degrees(math.atan2(d @ front, -(d @ up)))
        self.u_d0 = u_d
        self.rest_deg = self.meas(u_d)
        self.solved = {}
        # the view: image up along the proximal (body up for the shoulder), the bend to one side, the camera on the
        # limb's side of her body
        v = self.axis
        ey = perp(self.p3, v)
        if motion.startswith("shoulder"):
            ey = -ey
        ex = perp(self.b, v)
        ex = unit(ex - ey * (ex @ ey))
        cam = np.cross(ex, ey)
        if abs(v @ frame.lat) > 0.5 and cam @ out < 0:
            ex, cam = -ex, -cam
        self.ex, self.ey, self.cam = ex, ey, cam
        self.half = float(min(0.6 * max(self.Lp, self.Ld), 0.28))
        # selections (rest weights)
        D = poser.D
        chain = lambda nm: D[:, poser.subtree(I[nm])].sum(1)
        body = poser.piece == "body"
        other = "r" if s == "l" else "l"
        if motion in ("elbow", "knee"):
            rend = body & (chain(self.prox) >= 0.5)
            # the distal side by the rest geometry: the bisector plane at the joint
            self.seg_d = rend & (((poser.P0 - self.O) @ unit(-self.u_prox - self.u_d0)) < 0)
            self.seg_p = rend & ~self.seg_d
        elif motion.startswith("shoulder"):
            legs = chain(bone(poser, rig, "thigh", "l")) + chain(bone(poser, rig, "thigh", "r"))
            rend = body & (chain(bone(poser, rig, "upperarm", other)) < 0.5) & (legs < 0.5)
            self.seg_d = rend & (chain(self.bone) >= 0.5)
            self.seg_p = np.zeros_like(rend)
        else:
            arms = chain(bone(poser, rig, "upperarm", "l")) + chain(bone(poser, rig, "upperarm", "r"))
            # the other leg by the rest geometry too (seg_g's rule, mirrored): a weights change moved it (the hip
            # pin's trunk-weighted inner thigh of the other leg drew under this hip's corner at 90, 'outer' +40 mm)
            Oo = R[I[bone(poser, rig, "thigh", other)]][:3, 3]
            uo = unit(R[I[bone(poser, rig, "calf", other)]][:3, 3] - Oo)
            hips = 0.5 * (self.O + Oo)
            leg_o = (((poser.P0 - Oo) @ unit(up - uo)) < 0) & (((poser.P0 - hips) @ out) < 0)
            rend = body & ~leg_o & (arms < 0.5)
            self.seg_d = rend & (chain(self.bone) >= 0.5)
            self.seg_p = np.zeros_like(rend)
            # the girth's thigh by the rest geometry, not by weights (a weights change moved what was measured: the
            # hip pin took the inner thigh's top out of the thigh chain >= 0.5, rest girth d0.25 633 -> 547 mm, 90's
            # ratio 1.10 -> 1.24): her own side of the hips' midpoint, beyond the rest bisector plane at the joint
            # between the trunk's up and the thigh's rest direction (the knee and elbow's rule carried to the hip)
            self.seg_g = rend & (((poser.P0 - self.O) @ unit(up - u_d)) < 0) & (((poser.P0 - hips) @ out) > 0)
        T = poser.T
        self.rend = rend
        self.T_rend = T[rend[T].all(1)]
        self.near_m = rig.get("near_m", {}).get(motion, NEAR_M[motion])
        self.test = body & (np.linalg.norm(poser.P0 - self.O, axis=1) < self.near_m)
        self.cache = {}

    def turn(self, deg):
        """The rotation about self.axis that takes the distal bone's rest direction to the absolute angle `deg`."""
        if deg not in self.solved:
            wrap = lambda x: (x + 180) % 360 - 180
            signed = self.motion not in ("elbow", "knee")
            f = lambda t: (wrap(self.meas(rot(self.axis, t) @ self.u_d0) - deg) if signed
                           else self.meas(rot(self.axis, t) @ self.u_d0) - deg)
            ts = np.arange(-180, 180.01, 0.5)
            fs = [f(t) for t in ts]
            roots = []
            for i in range(len(ts) - 1):
                if fs[i] == 0 or fs[i] * fs[i + 1] < 0 and abs(fs[i] - fs[i + 1]) < 90:
                    lo, hi = ts[i], ts[i + 1]
                    for _ in range(40):
                        mid = (lo + hi) / 2
                        if f(lo) * f(mid) <= 0:
                            hi = mid
                        else:
                            lo = mid
                    roots.append((lo + hi) / 2)
            if not roots:
                raise ValueError(f"{self.motion} {self.s}: no turn reaches {deg} deg")
            if not signed:      # the flexing direction (the proximal's turn toward the distal about the axis)
                u = self.u_prox
                good = [t for t in roots if self.axis @ np.cross(u, rot(self.axis, t) @ self.u_d0) >= 0]
                roots = good or roots
            self.solved[deg] = min(roots, key=abs)
        return self.solved[deg]

    def turns(self, deg):
        return [] if deg == 0 else [(self.bone, rot(self.axis, self.turn(deg)))]

    def achieved(self, G):
        d = self.d3(G)
        return self.meas(d)

    def posed(self, deg):
        if deg not in self.cache:
            V, G, info = self.poser.pose(self.turns(deg))
            if deg:     # a poser that drives the pose further (the game's shoulder correction): chase the target
                aim = deg
                for _ in range(8):
                    err = self.achieved(G) - deg
                    if abs(err) < 0.1:
                        break
                    aim -= err
                    V, G, info = self.poser.pose([(self.bone, rot(self.axis, self.turn(aim)))])
            self.cache[deg] = (V, G, info)
        return self.cache[deg]

    def d3(self, G):
        return unit(G[self.je][:3, 3] - G[self.j][:3, 3])

    def view(self, px):
        h = self.half
        return ray.View(self.O, self.ex, self.ey, self.cam, px, -h, h, -h, h)

    # ---------------------------------------------------------------- sections --
    def sections(self, V, G):
        out = {}
        O = G[self.j][:3, 3]
        for seg, s in self.stations:
            if seg == "p":
                n, c, sel = self.p3, O + s * self.Lp * self.p3, self.seg_p
            else:
                d = self.d3(G)
                n, c, sel = d, O + s * self.Ld * d, getattr(self, "seg_g", self.seg_d)
            out[f"{seg}{s}"] = section(V, self.poser.T, sel, c, n, rend=self.rend)
        return out


def section(V, T, sel, c, n, rmax=0.15, rend=None):
    """The surface's cut by the plane (c, n), triangles touching `sel` (all their points in `rend`), near c:
    (hull perimeter m, enclosed area m^2; nan when the cut is open)."""
    T = T[sel[T].any(1) & (rend[T].all(1) if rend is not None else sel[T].all(1))]
    d = (V - c) @ n
    dt = d[T]
    cross = (dt.min(1) < 0) & (dt.max(1) > 0)
    T, dt = T[cross], dt[cross]
    if not len(T):
        return float("nan"), float("nan")
    P = V[T]
    segs = []
    for k in range(3):
        a, b = k, (k + 1) % 3
        da, db = dt[:, a], dt[:, b]
        m = (da < 0) != (db < 0)
        t = np.where(m, da / np.where(m, da - db, 1), 0)
        q = P[:, a] + t[:, None] * (P[:, b] - P[:, a])
        segs.append((m, q))
    pts = []
    A = np.zeros(len(T))
    q2 = np.zeros((len(T), 2, 3))
    cnt = np.zeros(len(T), int)
    for m, q in segs:
        for i in np.nonzero(m)[0]:
            if cnt[i] < 2:
                q2[i, cnt[i]] = q[i]
                cnt[i] += 1
    ok = cnt == 2
    q2, P, = q2[ok], P[ok]
    near = (np.linalg.norm(q2.mean(1) - c, axis=1) < rmax)
    q2, P = q2[near], P[near]
    if len(q2) < 8:
        return float("nan"), float("nan")
    # a closed cut only: every end shared by two pieces (an open cut, the selection's edge, has no area)
    ends = np.round(q2.reshape(-1, 3), 6)
    _, cnt_e = np.unique(ends, axis=0, return_counts=True)
    closed = (cnt_e == 1).sum() == 0
    tn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    tau = q2[:, 1] - q2[:, 0]
    flip = (np.cross(tau, n) * tn).sum(1) < 0
    a0 = np.where(flip[:, None], q2[:, 1], q2[:, 0]) - c
    a1 = np.where(flip[:, None], q2[:, 0], q2[:, 1]) - c
    area = float(0.5 * (np.cross(a0, a1) @ n).sum())
    e1 = perp(np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0]), n)
    e2 = np.cross(n, e1)
    pts = q2.reshape(-1, 3) - c
    xy = np.stack([pts @ e1, pts @ e2], 1)
    try:
        per = float(ConvexHull(xy).area)
    except Exception:
        per = float("nan")
    return per, (abs(area) if closed else float("nan"))


def normals(P, T):
    """Area-weighted point normals, welded by place (seams share one)."""
    _, inv = np.unique(np.round(P, 6), axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    N = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(N, inv[T[:, k]], fn)
    N = N[inv]
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def surface_depth(V, To, Q, chunk=400_000):
    """The true distance (m) from each point Q to the surface of the triangles To (indices into V): exact
    point-to-triangle (surfdist.closest_on_tris, Ericson's regions) over every triangle that can hold the closest
    point. Bound: the nearest of each triangle's samples (vertices, edge middles, centre) is an upper bound d_s on the
    true distance, and a triangle's closest point lies within its circumradius about its centre R_t <= R_max, so every
    triangle whose centre is within d_s + R_max is tested (no k-nearest guess)."""
    from surfdist import closest_on_tris
    A, B, C = V[To[:, 0]], V[To[:, 1]], V[To[:, 2]]
    S = np.concatenate([A, B, C, (A + B) / 2, (B + C) / 2, (C + A) / 2, (A + B + C) / 3])
    ds, _ = cKDTree(S).query(Q)
    cen = (A + B + C) / 3
    rmax = float(np.sqrt(np.max([((X - cen) ** 2).sum(1).max() for X in (A, B, C)])))
    cand = cKDTree(cen).query_ball_point(Q, ds + rmax + 1e-9)
    qi = np.concatenate([np.full(len(c), i, np.int64) for i, c in enumerate(cand)])
    ti = np.concatenate([np.asarray(c, np.int64) for c in cand])
    best = ds.copy()
    for a in range(0, len(qi), chunk):
        q_, t_ = qi[a:a + chunk], ti[a:a + chunk]
        x = closest_on_tris(Q[q_], A[t_], B[t_], C[t_])
        np.minimum.at(best, q_, np.linalg.norm(Q[q_] - x, axis=1))
    return best


def penetration(strip, V, T_all):
    """Posed body points near the joint inside the posed surface (the whole posed body and its closing head):
    count, and depth (mm) under the other segment's posed skin (the far side of the rest bisector plane)."""
    sc = ray.scene(V, T_all)
    idx = np.nonzero(strip.test)[0]
    N = normals(V, T_all)[idx]
    P = V[idx] + 3e-4 * N
    ins = ray.inside(sc, P)
    if not ins.any():
        return {"count": 0, "depth_max_mm": 0.0, "depth_p95_mm": 0.0, "tested": int(len(idx))}
    # depth: how far the point sits under the OTHER segment's skin. A fold presses the distal skin into the proximal
    # (or the reverse), so the surface it must leave by is the other side of the rest bisector plane (seg_d / seg_p).
    # Rays read the whole other limb (95-134 mm), and a rest-neighbour exclusion skipped the skin across the crease
    # (14-18 mm): the distance to the other side's posed triangles is the depth. P1 hip r4 (5 Nov): the true surface
    # distance (surface_depth, exact point-to-triangle), not the nearest of the triangles' samples (vertices, edge
    # middles, centres): a node pressed onto the other skin within 1 mm read 3-5 mm there (a measuring fix).
    q = idx[ins]
    sd = strip.seg_d
    T = strip.T_rend
    tri_d = sd[T].sum(1) >= 2
    dep, nfb = [], 0
    for side_d in (True, False):
        qs = q[sd[q] == side_d]
        if not len(qs):
            continue
        To = T[tri_d != side_d]
        if not len(To):
            nfb += len(qs)
            continue
        dep += list(surface_depth(V, To, V[qs]) * 1000)
    dep = np.array(dep)
    return {"count": int(ins.sum()), "depth_max_mm": round(float(dep.max()) if len(dep) else 0.0, 2),
            "depth_p95_mm": round(float(np.percentile(dep, 95)) if len(dep) else 0.0, 2), "tested": int(len(idx)), "depth_fallback": nfb}


# ------------------------------------------------------------------ outlines --
def rot2(v, deg):
    t = math.radians(deg)
    return np.array([v[0] * math.cos(t) - v[1] * math.sin(t), v[0] * math.sin(t) + v[1] * math.cos(t)])


class Plane2:
    """The strip's 2D side view at one angle: O at 0, the proximal and distal directions, their inner/outer normals."""

    def __init__(self, strip, G):
        vw = strip.view(1.0)
        O = G[strip.j][:3, 3]
        self.O = vw.xy(O[None])[0]
        p = unit(vw.xy((O + strip.p3)[None])[0] - self.O)
        d = unit(vw.xy((O + strip.d3(G))[None])[0] - self.O)
        b = unit(vw.xy((O + strip.b)[None])[0] - self.O)
        self.p, self.d = p, d
        self.b = unit(b - np.array([0.0, 1.0]) * b[1])   # the bend's side, square to image up
        n = np.array([-p[1], p[0]])
        self.n_in_p = n if n @ b > 0 else -n
        n = np.array([-d[1], d[0]])
        ref = p if abs(d @ p) < math.cos(math.radians(12)) else b
        self.n_in_d = n if n @ ref > 0 else -n
        self.Lp, self.Ld = strip.Lp, strip.Ld

    def dir(self, seg):
        return self.p if seg == "p" else self.d

    def normal(self, seg, side):
        n = self.n_in_p if seg == "p" else self.n_in_d
        return n if side == "in" else -n

    def L(self, seg):
        return self.Lp if seg == "p" else self.Ld


def scan(mask, vw, c, n, maxd=0.25):
    """From c (2D metres) along n: the distance to the mask's edge (m), or nan when c is not inside."""
    step = 0.25 / vw.px
    ts = np.arange(0, maxd, step)
    pts = c[None] + ts[:, None] * n[None]
    pix = vw.to_px(pts)
    j, i = np.floor(pix[:, 0]).astype(int), np.floor(pix[:, 1]).astype(int)
    ok = (i >= 0) & (i < mask.shape[0]) & (j >= 0) & (j < mask.shape[1])
    inside = np.zeros(len(ts), bool)
    inside[ok] = mask[i[ok], j[ok]]
    if not inside[0]:
        return float("nan")
    k = np.argmin(inside) if (~inside).any() else len(ts) - 1
    return float(ts[k])


def radii(strip, mask0, vw, pl0):
    """Rest half-widths per (seg, side, s) on the rest view's mask: the reference profiles' scale."""
    out = {}
    for seg in ("p", "d"):
        for side in ("in", "out"):
            for s in np.round(np.arange(0, 0.81, 0.05), 2):
                c = pl0.O + s * pl0.L(seg) * pl0.dir(seg)
                out[(seg, side, float(s))] = scan(mask0, vw, c, pl0.normal(seg, side))
    return out


def r_at(R, seg, side, s):
    ks = sorted(k[2] for k in R if k[0] == seg and k[1] == side)
    vals = [R[(seg, side, k)] for k in ks]
    ok = [(k, v) for k, v in zip(ks, vals) if np.isfinite(v)]
    if not ok:
        return float("nan")
    return float(np.interp(s, [k for k, _ in ok], [v for _, v in ok]))


def chaikin(P, fixed, it=3):
    P = np.asarray(P, float)
    fixed = list(fixed)
    for _ in range(it):
        Q, F = [P[0]], [fixed[0]]
        for a in range(len(P) - 1):
            if fixed[a + 1] and fixed[a]:
                Q.append(P[a + 1]); F.append(True)
                continue
            q, r = 0.75 * P[a] + 0.25 * P[a + 1], 0.25 * P[a] + 0.75 * P[a + 1]
            if not fixed[a]:
                Q.append(q); F.append(False)
            Q.append(r); F.append(False)
            if fixed[a + 1] or a + 1 == len(P) - 1:
                Q.append(P[a + 1]); F.append(True)
        P, fixed = np.array(Q), F
    return P


def build_ref(spec, pl, R, rest=None):
    """A reference profile json (tools/body/ref/<joint>_<angle>.json) built for this body: {curve: [N,2] metres}.
    `rest`: (rest mask, its view), for "rest" points (the rest outline where the motion does not reach: the trunk)."""
    out = {}
    for cname, pts in spec["curves"].items():
        P, fx = [], []
        for c in pts:
            mm = c.get("mm", 0.0) / 1000
            if "rest" in c:
                # the rest outline seen from the joint: rays at angles phi (deg) from image up away from the bend
                # (away from the bend: medial at the shoulder, back in a side view), first exit of the rest mask
                if rest is None:
                    continue
                m0, vw0 = rest
                a0, a1 = c["rest"]
                for phi in np.arange(a0, a1 + 1e-6, c.get("step", 3.0)):
                    t = math.radians(phi)
                    dv = math.cos(t) * np.array([0.0, 1.0]) - math.sin(t) * pl.b
                    r = scan(m0, vw0, pl.O, dv, maxd=0.3)
                    if np.isfinite(r):
                        P.append(pl.O + r * dv)
                        fx.append(False)
                continue
            if "arc" in c:
                n0, n1 = pl.normal("p", "out"), pl.normal("d", "out")
                a0, a1 = math.atan2(n0[1], n0[0]), math.atan2(n1[1], n1[0])
                # the outer way round: the sweep that does not pass through the inner normals' mean
                da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                mid_in = pl.normal("p", "in") + pl.normal("d", "in")
                trial = a0 + 0.5 * da
                if np.linalg.norm(mid_in) > 1e-6 and np.array([math.cos(trial), math.sin(trial)]) @ mid_in > 0:
                    da = da - math.copysign(2 * math.pi, da)
                a = a0 + c["arc"] * da
                rf = c.get("r_from", "mean")
                rp, rd = r_at(R, "p", "out", 0.0), r_at(R, "d", "out", 0.0)
                r = rd if rf == "d" else rp if rf == "p" else (rp + rd) / 2
                if not np.isfinite(r):
                    continue
                q = pl.O + (c.get("o", 1.0) * r + mm) * np.array([math.cos(a), math.sin(a)])
            elif "corner" in c:
                side = c["corner"] if c["corner"] in ("in", "out") else "in"
                s = c.get("s", 0.25)
                op = c.get("o", 1.0) * r_at(R, "p", side, s)
                od = c.get("o", 1.0) * r_at(R, "d", side, s)
                if not (np.isfinite(op) and np.isfinite(od)):
                    continue
                a1, d1 = pl.O + op * pl.normal("p", side), pl.p
                a2, d2 = pl.O + od * pl.normal("d", side), pl.d
                M = np.stack([d1, -d2], 1)
                if abs(np.linalg.det(M)) < 0.05:
                    continue
                t = np.linalg.solve(M, a2 - a1)
                q = (a1 + t[0] * d1 + c.get("mm_bisect", 0.0) / 1000 * unit(pl.normal("p", side) + pl.normal("d", side))
                     + c.get("mm_p", 0.0) / 1000 * pl.normal("p", side) + c.get("mm_d", 0.0) / 1000 * pl.normal("d", side))
            elif "tip" in c:
                # a bony point carried with the distal bone (the olecranon): placed where it stands at 90 degrees
                # (proud_mm beyond the proximal outer line, extrapolated from the "line" stations, past_mm beyond the
                # joint along the proximal), then turned with the distal segment to this angle
                s1, s2 = c.get("line", [0.12, 0.24])
                r1, r2 = r_at(R, "p", "out", s1), r_at(R, "p", "out", s2)
                past = c.get("past_mm", 20.0) / 1000
                sp = -past / pl.Lp
                w = r1 + (r2 - r1) * (sp - s1) / (s2 - s1) + c.get("proud_mm", 5.0) / 1000
                q = pl.O + (-w) * pl.d + past * pl.normal("d", "out")
            else:
                seg, side, s = c["seg"], c["side"], c["s"]
                if "line" in c:
                    s1, s2 = c["line"]
                    r1, r2 = r_at(R, seg, side, s1), r_at(R, seg, side, s2)
                    r = r1 + (r2 - r1) * (s - s1) / (s2 - s1)
                else:
                    r = r_at(R, seg, side, s)
                if not np.isfinite(r):
                    continue
                q = pl.O + s * pl.L(seg) * pl.dir(seg) + (c.get("o", 1.0) * r + mm) * pl.normal(seg, side)
            P.append(q)
            fx.append(bool(c.get("sharp", False)))
        if len(P) >= 2:
            fx[0] = fx[-1] = True
            out[cname] = chaikin(P, fx)
    return out


def resample(P, step=5e-4):
    P = np.asarray(P, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1], step)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1)


def deviation(ref, edge_xy, cap=0.04):
    """Reference curves against the model's outline points (2D metres): per curve, ref->model mean/max (mm), and
    model->ref max over the outline points nearest that curve away from its ends."""
    if not len(edge_xy) or not ref:
        return {}
    tr = cKDTree(edge_xy)
    dense = {k: resample(v) for k, v in ref.items()}
    owner = np.full(len(edge_xy), -1)
    best = np.full(len(edge_xy), np.inf)
    names = list(dense)
    near_idx = {}
    for ci, k in enumerate(names):
        d, i = cKDTree(dense[k]).query(edge_xy)
        near_idx[k] = (d, i)
        m = d < best
        best[m], owner[m] = d[m], ci
    out = {}
    for ci, k in enumerate(names):
        d_rm, _ = tr.query(dense[k])
        d, i = near_idx[k]
        m = (owner == ci) & (i > 2) & (i < len(dense[k]) - 3) & (d < cap)
        mr = d[m]
        out[k] = {"ref_to_model_mean_mm": round(float(d_rm.mean() * 1000), 2),
                  "ref_to_model_max_mm": round(float(d_rm.max() * 1000), 2),
                  "model_to_ref_max_mm": round(float(mr.max() * 1000), 2) if len(mr) else None,
                  "samples": int(len(d_rm))}
        out[k]["max_mm"] = round(max(out[k]["ref_to_model_max_mm"], out[k]["model_to_ref_max_mm"] or 0), 2)
        out[k]["mean_px"] = round(out[k]["ref_to_model_mean_mm"] * PX_CLOSE / 1000, 2)
        out[k]["max_px"] = round(out[k]["max_mm"] * PX_CLOSE / 1000, 2)
    return out


def edge_points(mask, vw):
    e = ray.boundary(mask)
    i, j = np.nonzero(e)
    return np.stack([vw.x0 + (j + 0.5) / vw.px, vw.y1 - (i + 0.5) / vw.px], 1)


def load_ref(motion, deg, ref_dir=HERE / "ref"):
    f = Path(ref_dir) / f"{motion}_{deg}.json"
    return json.loads(f.read_text()) if f.exists() else None


def pit(strip, V, r=0.025, reach=0.22):
    """hip_flex: the rest-curvature deviation at the r scale over the hip band (rend points within `reach` of the
    joint), posed minus rest, mm (+ = more concave than at rest: a dent), by region round the joint at rest (the
    angle in the lat-front plane: front |a| <= 45 deg, side 45..135 outward, back >= 135, medial the rest); fold
    contacts left out (points within 6 mm of a posed point that was over 4 cm away at rest: a crease is meant to
    change curvature). Derivation: (a) the D verdict's fix 2 (a pit facing the camera, which no outline sees); D2's
    harness (5 Nov) promoted: the same scale, band and exclusion, by region so the side of the hip reads on its own."""
    P0, T = strip.poser.P0, strip.poser.T
    if not hasattr(strip, "_pit0"):
        from gl import weld
        rep = weld(P0, 1e-6)
        sel = np.nonzero(strip.rend & (np.linalg.norm(P0 - strip.O, axis=1) < reach))[0]
        sel = sel[np.unique(rep[sel], return_index=True)[1]]
        nb = cKDTree(P0).query_ball_point(P0[sel], r)
        N0 = normals(P0, T)
        c0 = np.array([N0[i] @ (P0[j].mean(0) - P0[i]) for i, j in zip(sel, nb)])
        rel = P0[sel] - strip.O
        fr = strip.fr
        la = (rel @ fr.lat) * (1 if strip.s == "l" else -1)
        ang = np.degrees(np.arctan2(la, rel @ fr.front))
        reg = np.where(np.abs(ang) <= 45, "front", np.where(np.abs(ang) >= 135, "back", np.where(ang > 0, "side", "medial")))
        strip._pit0 = (sel, nb, c0, reg, np.stack([la, rel @ fr.up, rel @ fr.front], 1))
    sel, nb, c0, reg, at = strip._pit0
    N = normals(V, T)
    c1 = np.array([N[i] @ (V[j].mean(0) - V[i]) for i, j in zip(sel, nb)])
    dv = (c1 - c0) * 1000
    dd, ii = cKDTree(V).query(V[sel], k=48)
    far = np.linalg.norm(P0[ii] - P0[sel][:, None], axis=2) > 0.04
    fold = (np.where(far, dd, 9) < 0.006).any(1)
    out = {"pit_mm": None, "by_region_mm": {}, "at_cm": {}, "fold_points": int(fold.sum())}
    for g in ("front", "side", "back", "medial"):
        m = (reg == g) & ~fold
        if m.any():
            k = int(np.argmax(np.where(m, dv, -1e9)))
            out["by_region_mm"][g] = round(float(dv[k]), 2)
            out["at_cm"][g] = np.round(at[k] * 100, 1).tolist()   # out, up, front of the joint at rest (cm)
    if out["by_region_mm"]:
        out["pit_mm"] = max(out["by_region_mm"].values())
    return out


# ------------------------------------------------------------------ the run --
def run_strip(strip, angles=ANGLES, ref_dir=HERE / "ref", T_all=None):
    """Every number of one strip, and what its sheet draws."""
    poser = strip.poser
    T_all = poser.T if T_all is None else T_all
    vw_hi = strip.view(2 * PX_CLOSE)
    V0, G0, _ = strip.posed(0)
    m0 = ray.mask(V0, strip.T_rend, vw_hi)
    pl0 = Plane2(strip, G0)
    R = radii(strip, m0, vw_hi, pl0)
    sec0 = strip.sections(V0, G0)
    res = {"bone": strip.bone, "end": strip.end, "axis": np.round(strip.axis, 4).tolist(),
           "rest_angle_deg": round(strip.rest_deg, 1), "Lp_mm": round(strip.Lp * 1000, 1), "Ld_mm": round(strip.Ld * 1000, 1),
           "angles": {}}
    draw = {}
    extra = tuple(d for d in EXTRA.get(strip.motion, ()) if d not in angles) if tuple(angles) == ANGLES else ()
    for deg in tuple(angles) + extra:
        V, G, info = strip.posed(deg)
        sec = strip.sections(V, G)
        row = {"girth_mm": {}, "girth_ratio": {}, "area_ratio": {}}
        for k, (per, area) in sec.items():
            per0, area0 = sec0[k]
            row["girth_mm"][k] = round(per * 1000, 1) if np.isfinite(per) else None
            row["girth_ratio"][k] = round(per / per0, 4) if np.isfinite(per) and np.isfinite(per0) and per0 > 0 else None
            row["area_ratio"][k] = round(area / area0, 4) if np.isfinite(area) and np.isfinite(area0) and area0 > 0 else None
        row["penetration"] = penetration(strip, V, T_all)
        if strip.motion == "hip_flex":
            row["pit"] = pit(strip, V)
        if deg in extra:
            row["drawn"] = False
        mk = ray.mask(V, strip.T_rend, vw_hi)
        pl = Plane2(strip, G)
        bend2 = math.degrees(math.acos(np.clip(pl.d @ pl0.d, -1, 1)))
        row["bend_in_view_deg"] = round(bend2, 1)
        row["poser"] = info
        row["target_deg"] = deg
        row["achieved_deg"] = round(strip.achieved(G), 2)
        spec = load_ref(strip.motion, deg, ref_dir) if deg else None
        ref = build_ref(spec, pl, R, (m0, vw_hi)) if spec else {}
        edge = edge_points(mk, vw_hi)
        row["outline_vs_ref"] = deviation(ref, edge) if ref else None
        row["outline_mm"] = outline_samples(mk, vw_hi, pl)
        res["angles"][str(deg)] = row
        if deg not in extra:
            draw[deg] = (V, ref)
    return res, draw


def outline_samples(mask, vw, pl):
    """The side view's outline as polylines: per segment and side, (s of the segment, mm out from the bone line)."""
    out = {}
    for seg in ("p", "d"):
        for side in ("in", "out"):
            pts = []
            for s in np.round(np.arange(0.05, 0.61, 0.05), 2):
                c = pl.O + s * pl.L(seg) * pl.dir(seg)
                r = scan(mask, vw, c, pl.normal(seg, side))
                if np.isfinite(r):
                    pts.append([float(s), round(r * 1000, 1)])
            out[f"{seg}_{side}"] = pts
    return out


def clay(V, T, view, light=None):
    """The sheets' clay, lambert, SMOOTH: each pixel's normal interpolated from its triangle's welded point normals
    (barycentrics of the hit point), as the game's renderer shades the body. ray.clay shades each triangle flat and
    two-sided: on a strip it drew the quad rings as bands (the deltoid's loops, the hip's seam row: the D verdict's
    "split shading at seams") and a non-planar quad's two triangles as crosshatching (the right shoulder: its quads
    split on the other diagonal from the left's); neither is in the mesh's own normals. Two-sided, as ray.clay (a
    strip's dropped parts show the body's inside through their hole)."""
    sc = ray.scene(V, T)
    pid, tf = view.cast(sc)
    m = pid >= 0
    img = np.ones(pid.shape)
    if light is None:
        light = 0.75 * view.cam + 0.45 * view.ey - 0.3 * view.ex
    light = light / np.linalg.norm(light)
    x, y = view.grid()
    org = view.o + x[..., None] * view.ex + y[..., None] * view.ey + 5.0 * view.cam
    hit = (org - np.where(m, tf, 0.0)[..., None] * view.cam)[m]
    tri = T[pid[m]]
    A, B, C = V[tri[:, 0]], V[tri[:, 1]], V[tri[:, 2]]
    v0, v1, v2 = B - A, C - A, hit - A
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
    b1 = (d11 * d20 - d01 * d21) / den
    b2 = (d00 * d21 - d01 * d20) / den
    b0 = 1 - b1 - b2
    Nv = normals(V, T)
    n = b0[:, None] * Nv[tri[:, 0]] + b1[:, None] * Nv[tri[:, 1]] + b2[:, None] * Nv[tri[:, 2]]
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    n = np.where((n @ view.cam)[:, None] < 0, -n, n)
    img[m] = 0.18 + 0.62 * np.clip(n @ light, 0, 1) + 0.08 * np.clip(n @ view.cam, 0, 1)
    return img, m


def shade_steps(img, m, edge_px=3):
    """The clay's pixel-to-pixel shading step inside the mask, the outline's edge_px dropped: p99 and max (0..1)."""
    from scipy.ndimage import binary_erosion
    core = binary_erosion(m, iterations=edge_px)
    gx = np.abs(np.diff(img, axis=1))[core[:, 1:] & core[:, :-1]]
    gy = np.abs(np.diff(img, axis=0))[core[1:] & core[:-1]]
    g = np.concatenate([gx, gy])
    return round(float(np.percentile(g, 99)), 4), round(float(g.max()), 4)


def sheet(strips_draw, path, title):
    """One PNG per joint: rows = sides, columns = rest | 90 | 135; clay at the close-up scale, the model's outline
    (orange) and the reference (cyan)."""
    from PIL import Image, ImageDraw
    rows = []
    for strip, draw in strips_draw:
        vw = strip.view(PX_CLOSE)
        panels = []
        for deg in sorted(draw):
            V, ref = draw[deg]
            img, m = clay(V, strip.T_rend, vw)
            rgb = np.stack([img * 255] * 3, -1).astype(np.uint8)
            e = ray.boundary(m)
            rgb[e] = (235, 120, 30)
            im = Image.fromarray(rgb)
            dr = ImageDraw.Draw(im)
            for curve in ref.values():
                px = vw.to_px(curve)
                dr.line([tuple(p) for p in px], fill=(20, 170, 220), width=1)
            dr.text((4, 3), f"{strip.motion} {strip.s.upper()} {deg}", fill=(0, 0, 0))
            panels.append(im)
        rows.append(panels)
    W = sum(p.width for p in rows[0]) + 4 * (len(rows[0]) - 1)
    H = sum(r[0].height for r in rows) + 4 * (len(rows) - 1) + 16
    out = Image.new("RGB", (W, H), (255, 255, 255))
    ImageDraw.Draw(out).text((4, 2), title, fill=(0, 0, 0))
    y = 16
    for r in rows:
        x = 0
        for p in r:
            out.paste(p, (x, y))
            x += p.width + 4
        y += r[0].height + 4
    out.save(path)
    return out.size
