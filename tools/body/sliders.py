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
            if v:
                V += self.delta(n, v)
        return V
