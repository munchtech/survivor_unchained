# k12a3: death_back held at heading pi, so the clip's own head turn (to her left) faces the coals; s3 at ground level
# west of her face. V: the clip's head; W: plus a head turn to the ground before her face.
import importlib.util, os
H = os.path.dirname(os.path.abspath(__file__))
def _load(n):
    spec = importlib.util.spec_from_file_location(n, os.path.join(H, n + ".py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
v1, v2 = _load("v_k12a1"), _load("v_k12a2")
ROOT = [-9.31, 89.235, 3.1416]
HEAD = [-9.45, 0.17, 90.45]


def cam3(fn0):
    def fn(shots, f):
        fn0(shots, f)
        shots["3"]["cam"] = {"pos": [-10.07, 0.13, 90.5], "at": HEAD, "lens": 60, "focus": {"actor": "her", "bone": "head"}, "fstop": 2.0}
    return fn


VARIANTS = {
    "V": cam3(v2.lying("her/death_back", 1.33, ROOT, None)),
    "W": cam3(v2.lying("her/death_back", 1.33, ROOT, [-10.1, 0.0, 90.5])),
}
