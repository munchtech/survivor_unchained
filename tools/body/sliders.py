"""Our body sliders (catalogue.json) resolved into MakeHuman macros and targets for mh_base.make_base.

    resolve(spec) -> (macros, targets): the spec's own macros with each slider's macro offsets added (clipped 0..1,
    MPFB then evaluates them as its own nonlinear blends: nothing is linearised here) and the targets each slider
    lays, summed by name (a pair [decr, incr, k]: k |v| on the side of v's sign; "lr": the l- and r- target alike).
A spec with no "sliders" resolves to its own macros and no targets.

    load_spec(path): a spec; one with "base" (a spec's path from the repo) is that spec with its own keys laid over.
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def load_spec(path):
    with open(path) as f:
        spec = json.load(f)
    if "base" in spec:
        b = load_spec(os.path.join(REPO, spec["base"]))
        b.update({k: v for k, v in spec.items() if k != "base"})
        return b
    return spec


def catalogue():
    with open(os.path.join(HERE, "catalogue.json")) as f:
        return json.load(f)["sliders"]


DESIGNED_DIR = os.path.join(HERE, "designed")


def designed():
    """OUR targets (no MakeHuman, no bake): catalogue.json "designed" (the first two rules, 5 Nov) and then every
    tools/body/designed/*.json form file's "sliders" (P1 R1: the form library), in each entry's "order" (then name).
    Rules on our vertices, evaluated after the sampled sliders (see OurSliders._designed); rule "field" is the form
    library's: moves under smooth (C2) region masks on our topology's reference surface (OurSliders.field_delta)."""
    with open(os.path.join(HERE, "catalogue.json")) as f:
        out = dict(json.load(f).get("designed", {}))
    more = []
    if os.path.isdir(DESIGNED_DIR):
        for fn in sorted(os.listdir(DESIGNED_DIR)):
            if fn.endswith(".json"):
                with open(os.path.join(DESIGNED_DIR, fn)) as f:
                    for n, c in json.load(f).get("sliders", {}).items():
                        assert n not in out and n not in dict(more), ("designed slider twice", n, fn)
                        c = dict(c)
                        c["_file"] = fn
                        more.append((n, c))
    more.sort(key=lambda nc: (nc[1].get("order", 100), nc[0]))
    out.update(more)
    return out


def head_move(values, des=None):
    """The head's placement (m, glTF): the sum over the designed sliders of "head_move" [dx, dy, dz] times the slider's
    value (clipped to its range). build_topo moves the baked head by it before the ring is placed, so a neck slider
    that lifts the ring lifts the head the same (the ring stays the head's, one to one)."""
    des = designed() if des is None else des
    m = [0.0, 0.0, 0.0]
    for n, c in des.items():
        v = float(values.get(n, 0.0) or 0.0)
        if v and "head_move" in c:
            lo, hi = c["range"]
            v = min(max(v, lo), hi)
            m = [a + v * float(b) for a, b in zip(m, c["head_move"])]
    return m


def smoother(t):
    """C2 ramp 0..1 (quintic smootherstep): the form library's mask edge (smoothstep is only C1: its curvature jumps
    at the ends, which a painted-cel terminator shows as a kink)."""
    import numpy as np
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def resolve(spec, cat=None):
    cat = cat or catalogue()
    macros = copy.deepcopy(spec["macros"])
    targets = {}
    for name, v in spec.get("sliders", {}).items():
        c = cat[name]
        lo, hi = c["range"]
        v = min(max(float(v), lo), hi)
        for m, k in c.get("macros", {}).items():
            macros[m] = min(max(macros[m] + k * v, 0.0), 1.0)
        for decr, incr, k in c.get("pairs", []):
            a = k * v
            t, w = (incr, a) if a > 0 else (decr, -a)
            if w == 0:
                continue
            for n in ([f"l-{t}", f"r-{t}"] if c.get("lr") else [t]):
                targets[n] = targets.get(n, 0.0) + w
    return macros, targets


class OurSliders:
    """The catalogue's sliders on OUR topology (P1 B1: slider_bake.py's tools/body/base/sliders_{tier}.npz), numpy only:
    no MakeHuman, no Blender. evaluate({name: v}) -> our vertices [n, 3] (glTF, the reference's frame) = the reference
    (V0) plus, per slider, the piecewise-linear blend of its stored samples (0 at v = 0; v clipped to the stored
    samples' span, which is the catalogue's range), the sliders summed. delta(name, v) -> that slider's move alone."""

    def __init__(self, path):
        import numpy as np
        self.np = np
        z = np.load(path)
        self.V0 = z["V0"].astype(np.float64)
        self.names = [str(n) for n in z["names"]]
        self.knots, self.D = {}, {}
        for n in self.names:
            v, d = z[f"v:{n}"], z[f"d:{n}"].astype(np.float64) * (float(z["d_unit_m"]) if "d_unit_m" in z.files else 1.0)
            k = np.argsort(np.append(v, 0.0))
            self.knots[n] = np.append(v, 0.0)[k]
            self.D[n] = np.concatenate([d, np.zeros((1,) + d.shape[1:])])[k]
        self.designed = designed()
        self.names += [n for n in self.designed if n not in self.names]
        self._fields = {}
        self._fd = {}
        self._topo = None
        self.path = path

    def topo(self):
        """Our topology for this bake (out/topo/<tier>.npz, the tier from the bake's file name): quads, the open neck
        ring, the reference V0's vertex normals. Asserted to be the bake's V0."""
        np = self.np
        if self._topo is None:
            tier = os.path.splitext(os.path.basename(self.path))[0].split("_")[-1]
            z = np.load(os.path.join(HERE, "out", "topo", f"{tier}.npz"))
            Q = z["Q"].astype(np.int64)
            assert np.abs(z["V"] - self.V0).max() < 1e-6, "the topology is not the bake's"
            e = np.sort(np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]]), 1)
            u, c = np.unique(e, axis=0, return_counts=True)
            ring = np.unique(u[c == 1])
            V = self.V0
            fn = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
            N = np.zeros_like(V)
            for k in range(4):
                np.add.at(N, Q[:, k], fn)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
            self._topo = {"Q": Q, "ring": ring, "N": N, "tier": tier}
        return self._topo

    def delta(self, name, v):
        np = self.np
        x = self.knots[name]
        v = float(min(max(v, x[0]), x[-1]))
        i = int(np.clip(np.searchsorted(x, v) - 1, 0, len(x) - 2))
        t = (v - x[i]) / (x[i + 1] - x[i])
        return (1 - t) * self.D[name][i] + t * self.D[name][i + 1]

    def evaluate(self, values, post=None):
        """The body at these slider values. post=None: every slider; False: all but the designed "post_join" ones
        (build_topo stage 1 lays those after the head join: post_delta); True: V0 + post_delta alone."""
        V = self.V0.copy()
        if post is True:
            return V + self.post_delta(values)
        for n, v in values.items():
            if v and n not in self.designed:
                V += self.delta(n, v)
        for n, c in self.designed.items():     # catalogue order: each rule on the body the ones before it made
            v = values.get(n, 0.0)
            if v and not (post is False and c.get("post_join")):
                lo, hi = c["range"]
                V = self._designed(c, min(max(float(v), lo), hi), V, values)
        return V

    def post_delta(self, values):
        """The designed "post_join" sliders' move (rules "field" and "target": both linear in v), laid by build_topo after
        the slider join and the stance, so the neck's own fields reach the ring (the join holds every other move off it)
        and move it with the head (head_move), and a sculpted target (her_a) lands on the joined body it was made from."""
        D = self.np.zeros_like(self.V0)
        for n, c in self.designed.items():
            v = values.get(n, 0.0)
            if v and c.get("post_join"):
                assert c["rule"] in ("field", "target"), ("post_join needs a linear rule", n)
                lo, hi = c["range"]
                D += min(max(float(v), lo), hi) * (self.field_delta(n) if c["rule"] == "field" else self.target_delta(c))
        return D

    # ---------------------------------------------------------------------------- rule "field": the form library --
    def coord(self, on, P):
        """A mask's coordinate on the reference V0 (glTF m: x left+, y up, z front+): "x", "ax" (|x|: both sides
        alike), "y", "z", "ring" (the distance to the open neck ring's nearest point), "ring_y" (the height above the
        ring's lowest point), "neck_r" (the horizontal distance to the ring centroid's vertical axis)."""
        np = self.np
        if on == "x":
            return P[:, 0]
        if on == "ax":
            return np.abs(P[:, 0])
        if on in ("y", "z"):
            return P[:, "xyz".index(on)]
        R = self.V0[self.topo()["ring"]]
        if on == "ring":
            from scipy.spatial import cKDTree
            return cKDTree(R).query(P)[0]
        if on == "ring_y":
            return P[:, 1] - R[:, 1].min()
        if on == "neck_r":
            c = R.mean(0)
            return np.hypot(P[:, 0] - c[0], P[:, 2] - c[2])
        raise KeyError(on)

    def mask(self, terms, P):
        """A region mask 0..1, the product of its terms, each a C2 window on one coordinate:
        {"on": coord, "full": [a, b], "fade": f | [f_lo, f_hi]}: 1 on [a, b], easing (smoother) to 0 at a - f_lo and
        at b + f_hi (a null end is open); or {"on": "ell", "c": [x, y, z], "r": [rx, ry, rz], "full": k}: 1 inside
        the ellipsoid scaled by k, easing to 0 at its surface (x mirrored: |x| against c's x)."""
        np = self.np
        m = np.ones(len(P))
        for t in terms:
            if t["on"] == "ell":
                c, r = np.asarray(t["c"], float), np.asarray(t["r"], float)
                Q = P.copy()
                Q[:, 0] = np.abs(Q[:, 0])
                rho = np.linalg.norm((Q - c) / r, axis=1)
                k = t.get("full", 0.0)
                m *= 1.0 - smoother((rho - k) / max(1.0 - k, 1e-9))
                continue
            x = self.coord(t["on"], P)
            a, b = t["full"]
            f = t.get("fade", 0.0)
            flo, fhi = (f, f) if not isinstance(f, (list, tuple)) else f
            if a is not None:
                m *= smoother((x - (a - flo)) / flo) if flo > 0 else (x >= a)
            if b is not None:
                m *= smoother(((b + fhi) - x) / fhi) if fhi > 0 else (x <= b)
        return m

    def centre(self, c):
        np = self.np
        if c == "ring":
            return self.V0[self.topo()["ring"]].mean(0) * np.array([0.0, 1.0, 1.0])
        return np.asarray(c, float)

    def field_delta(self, name):
        """Rule "field" (P1 R1, the form library): the slider's move at v = 1, a sum of moves, each its own C2 mask
        (mask()) on the reference V0 times a move: "translate" [dx, dy, dz] (dx away from the midline on each side),
        "scale" {"c": [cx, cy, cz] | "ring", "k": [kx, ky, kz]} (about the centre per axis; cx 0 keeps the mirror),
        "radial" {"c": ..., "m": m} (horizontally away from the centre's vertical axis), "normal" m (along V0's
        normal). Linear in v: a designed blend target on our topology, the same rule on every body and both tiers (the
        masks live on the reference surface both tiers share)."""
        np = self.np
        if name not in self._fd:
            c = self.designed[name]
            P = self.V0
            sx = np.where(P[:, 0] >= 0, 1.0, -1.0)
            D = np.zeros_like(P)
            for mv in c["moves"]:
                w = self.mask(mv["mask"], P)
                d = np.zeros_like(P)
                if "translate" in mv:
                    d += np.asarray(mv["translate"], float)[None, :] * np.stack([sx, np.ones_like(sx), np.ones_like(sx)], 1)
                if "scale" in mv:
                    d += (P - self.centre(mv["scale"]["c"])) * (np.asarray(mv["scale"]["k"], float) - 1.0)[None, :]
                if "radial" in mv:
                    h = P - self.centre(mv["radial"]["c"])
                    h[:, 1] = 0.0
                    h /= np.maximum(np.linalg.norm(h, axis=1, keepdims=True), 1e-9)
                    d += h * float(mv["radial"]["m"])
                if "normal" in mv:
                    d += self.topo()["N"] * float(mv["normal"])
                D += w[:, None] * d
            self._fd[name] = D
        return self._fd[name]

    def field(self, c):
        """A designed rule's mass field per side: the |move| of its source slider at the source value, 0..1 (the
        part of the body that slider IS: the breast for bust_size, the buttock for glutes), smoothstepped above a
        floor so the rim never moves; sides by the sign of x."""
        np = self.np
        key = (c["field"], c.get("field_v", 1.0), c.get("floor", 0.1))
        if key not in self._fields:
            m = np.linalg.norm(self.delta(c["field"], c.get("field_v", 1.0)), axis=1)
            t = np.clip((m / m.max() - key[2]) / (1.0 - key[2]), 0.0, 1.0)
            self._fields[key] = t * t * (3.0 - 2.0 * t)
        return self._fields[key]

    def target_delta(self, c):
        """Rule "target": a form SCULPTED ONCE as a source file on our topology (like base/hand_l.obj): "file" a path
        from the repo with {tier} -> an npz with "D" [n, 3] (the move at v = 1, glTF m) and "topology" (topo_sha of the
        tier it was made on, asserted). Each tier's file is made by the target's own generator (its "made_by"); a
        close-only source reaches play by sliders.carry_to_tier."""
        np = self.np
        key = ("target", c["file"])
        if key not in self._fd:
            p = os.path.join(REPO, c["file"].format(tier=self.topo()["tier"]))
            z = np.load(p)
            D = z["D"].astype(np.float64)
            assert D.shape == self.V0.shape, ("target size", p, D.shape)
            self._fd[key] = D
        return self._fd[key]

    def _designed(self, c, v, V, values=None):
        if c["rule"] == "field":
            return V + v * self.field_delta(next(k for k, x in self.designed.items() if x is c))
        if c["rule"] == "target":
            return V + v * self.target_delta(c)
        if c["rule"].startswith("py:"):
            # a designed rule in its own module (tools/body/<module>.py, function f(sl, c, v, V, values) -> new V):
            # the form library's richer fields (a breast volume by its profile curves...), its numbers in the JSON
            import importlib
            mod, fn = c["rule"][3:].rsplit(".", 1)
            return getattr(importlib.import_module(mod), fn)(self, c, v, V, values or {})
        if c["rule"] == "growth_turn":
            return V + v * self._growth_turn(c, float((values or {}).get(c["field"], 0.0)))
        """rule "mass_lift": each side's mass (the field) is carried up toward its root, more the lower it sits (0 at
        the field's top, full at its bottom, smoothstepped): the mass shortens and rounds, its under-curve rises
        off the fold it hung into, the root never moves; the lower part also comes out from the wall it hangs
        from ("out_m": the breast's point turns from down to forward, the buttock's under-curve rounds); "fill" adds
        the source slider's own move at the core (w squared: none at the rim). A smooth vertical ramp, not a turn
        about a hinge: a turn lifts the upper pole's front by its depth and folds it into a shelf (measured, 5 Nov)."""
        np = self.np
        assert c["rule"] == "mass_lift", c["rule"]
        w = self.field(c)
        src = self.delta(c["field"], c.get("field_v", 1.0))
        out = V.copy()
        for side in (1.0, -1.0):
            s = (np.sign(V[:, 0]) == side) & (w > 0)
            if not s.any():
                continue
            ws, P = w[s], V[s]
            fz = np.sign(np.average(src[s][:, 2], weights=ws))       # +1: the mass faces front (z+), -1: back
            top = np.percentile(P[ws > 0.05, 1], c.get("root_pct", 98))
            low = np.percentile(P[ws > 0.05, 1], 2)
            g = np.clip((top - P[:, 1]) / (top - low), 0.0, 1.0)
            g = g * g * (3.0 - 2.0 * g)
            d = np.zeros_like(P)
            d[:, 1] = v * c["lift_m"] * ws * g
            d[:, 2] = fz * v * c.get("out_m", 0.0) * ws * g
            if c.get("fill"):
                d += src[s] * (v * c["fill"] * ws * ws)[:, None]
            if c.get("midline_m"):
                # nothing moves toward the midline and the move fades out at it: the two buttocks' fill met in the
                # cleft (12-14 points inside at rest, quads folded to 178 deg; check 5 Nov)
                d[:, 0] = np.where(side * d[:, 0] < 0.0, 0.0, d[:, 0])
                m = np.clip(np.abs(P[:, 0]) / c["midline_m"], 0.0, 1.0)
                d *= (m * m * (3.0 - 2.0 * m))[:, None]
            out[s] = P + d
        return out

    def _growth_turn(self, c, sv):
        """rule "growth_turn" (bust_lift): MakeHuman's cup grows the breast mostly DOWN (bust_size +1: 91 mm at the
        lower pole, its mean move 70 deg below forward): its mass slides down the chest, the lower pole hangs past the
        fold into a deep flat shelf and the upper pole hollows. Ours turns that same growth (the source slider's move
        at its current value, positive only) up toward forward about the left-right axis, each move by its own angle:
        "turn_deg" where the growth already leans forward (the upper pole and the point: it fills the upper pole and
        brings the point forward and up) to "turn_low_deg" where it points straight down (the lower pole: it rounds
        out forward instead of hanging, the shelf tilts up into a curve); "scale" sizes the turned growth (1: each move
        keeps its length, so the breast grows forward by what it hung: the volume rises). The move is the slider's own
        smooth field turned, so it is as smooth as MakeHuman's target (no hinge, no ramp edge, no rim: 0 where the
        cup does not move); mirrored sides alike (a turn about x). Returns the change at v = 1."""
        np = self.np
        if sv <= 0:
            return np.zeros_like(self.V0)
        g = self.delta(c["field"], sv)
        dn, fw = -g[:, 1], g[:, 2]
        a = np.degrees(np.arctan2(fw, np.maximum(dn, 1e-9)))            # the move's lean from straight down
        lo, hi = c.get("lean_deg", [0.0, 40.0])
        t = np.clip((hi - a) / (hi - lo), 0.0, 1.0)
        t = t * t * (3.0 - 2.0 * t)                                        # 1 where it points down, 0 leaning fwd
        th = np.radians(c["turn_deg"] + (c["turn_low_deg"] - c["turn_deg"]) * t)
        k = c.get("scale", 1.0)
        out = np.zeros_like(g)
        out[:, 0] = (k - 1.0) * g[:, 0]
        out[:, 1] = k * (g[:, 1] * np.cos(th) + g[:, 2] * np.sin(th)) - g[:, 1]
        out[:, 2] = k * (-g[:, 1] * np.sin(th) + g[:, 2] * np.cos(th)) - g[:, 2]
        return out


def carry_to_tier(D_from, tier_from="close", tier_to="play", k=6):
    """A per-vertex move made on one tier (a sculpted target's D) carried to another: both tiers' reference V0 lie on
    the same reference surface, so each target vertex takes the inverse-distance blend of its k nearest source
    vertices' moves (smooth: the source's spacing is under the target's). Returns D on tier_to's vertices."""
    import numpy as np
    from scipy.spatial import cKDTree
    a = np.load(os.path.join(HERE, "base", f"sliders_{tier_from}.npz"))["V0"].astype(np.float64)
    b = np.load(os.path.join(HERE, "base", f"sliders_{tier_to}.npz"))["V0"].astype(np.float64)
    d, i = cKDTree(a).query(b, k=k)
    w = 1.0 / np.maximum(d, 1e-5) ** 2
    w /= w.sum(1, keepdims=True)
    return (np.asarray(D_from, float)[i] * w[..., None]).sum(1)


def relax(sl, V, values):
    """The designed sliders' "relax" (laid by build_topo last in stage 1): a field that moves a region a lot stretches
    its quads (the neck's rows under the held ring); this evens them by tangential Laplacian smoothing on our quads'
    graph (each step moves a point toward its neighbours' mean with the normal part taken off, so the surface keeps
    its shape and only the points slide), weighted by the region's mask on V0; the open ring is pinned. Entry:
    "relax": {"mask": [...], "iters": n, "step": 0..1}, active when the slider is non-zero."""
    import numpy as np
    jobs = [(n, c["relax"]) for n, c in sl.designed.items() if c.get("relax") and values.get(n, 0.0)]
    if not jobs:
        return V
    t = sl.topo()
    Q = t["Q"]
    n = len(V)
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    e = np.unique(np.sort(e, 1), axis=0)
    import scipy.sparse as sp
    A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    V = V.copy()
    for name, r in jobs:
        w = sl.mask(r["mask"], sl.V0) * float(r.get("step", 0.5))
        w[t["ring"]] = 0.0
        act = w > 1e-4
        for _ in range(int(r.get("iters", 20))):
            fn = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
            N = np.zeros_like(V)
            for k in range(4):
                np.add.at(N, Q[:, k], fn)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
            L = (A @ V) / np.maximum(deg, 1)[:, None] - V
            L -= (L * N).sum(1, keepdims=True) * N
            V[act] += w[act, None] * L[act]
    return V
