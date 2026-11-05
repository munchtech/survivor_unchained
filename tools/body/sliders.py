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


def designed():
    """catalogue.json "designed": OUR targets (no MakeHuman, no bake), rules on our vertices evaluated after the
    sampled sliders on the current body (see OurSliders._designed)."""
    with open(os.path.join(HERE, "catalogue.json")) as f:
        return json.load(f).get("designed", {})


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

    def delta(self, name, v):
        np = self.np
        x = self.knots[name]
        v = float(min(max(v, x[0]), x[-1]))
        i = int(np.clip(np.searchsorted(x, v) - 1, 0, len(x) - 2))
        t = (v - x[i]) / (x[i + 1] - x[i])
        return (1 - t) * self.D[name][i] + t * self.D[name][i + 1]

    def evaluate(self, values):
        V = self.V0.copy()
        for n, v in values.items():
            if v and n not in self.designed:
                V += self.delta(n, v)
        for n, c in self.designed.items():     # catalogue order: each rule on the body the ones before it made
            v = values.get(n, 0.0)
            if v:
                lo, hi = c["range"]
                V = self._designed(c, min(max(float(v), lo), hi), V, values)
        return V

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

    def _designed(self, c, v, V, values=None):
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
