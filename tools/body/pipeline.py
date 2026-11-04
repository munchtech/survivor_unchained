"""Stages 2-6 of the base build (build.py): pure numpy/scipy, run inside Blender or out."""
import json
import os
import time

import numpy as np
import scipy.sparse as sp

import headmatch as hm
from gl import Glb
from subdiv import subdivide

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HEADS = ["HeroineEyes", "HeroineHead", "HeroineLashes", "HeroineTeeth", "HeroineTongue"]


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def eye_smooth(V, EV, sim):
    """Her head's smoothing amounts (heroine_head.py): none within 1.4 cm of each eye's middle, all by 2.4 cm."""
    P, E = hm.place(V, sim), hm.place(EV, sim)
    ec = [E[E[:, 0] * sd > 0].mean(0) for sd in (1, -1)]
    return smooth01((np.min([np.linalg.norm(P - c, axis=1) for c in ec], 0) - 0.014) / 0.010)


def stage_place(base, A, rep):
    """2: the similarity and the head's correspondence."""
    V, F, U, EV = base["V"], base["F"], base["U"], base["eyes"]
    head = A.mesh("HeroineHead")
    HP = hm.to_blender(head.P)
    Sub0, _, _ = subdivide(len(V), F, U, None)
    sim = hm.rough_place(Sub0 @ V, HP)
    cache = {}

    def points(sim_):
        sm = eye_smooth(V, EV, sim_)
        Sub, F2, U2 = subdivide(len(V), F, U, sm)
        cache.update(Sub=Sub, F2=F2, U2=U2, smooth=sm)
        return Sub @ V
    sim, P2, st = hm.refine_place(points, HP, sim)
    rep_ = hm.weld_rep(head.P)
    uniq = np.unique(rep_)
    remap = -np.ones(len(rep_), np.int64)
    remap[uniq] = np.arange(len(uniq))
    HPw, HT = HP[uniq], remap[rep_[head.T]]
    Pp = hm.place(P2, sim)
    match, head_quads, info = hm.correspond(Pp, cache["F2"], HPw, HT)
    s, R, T = sim
    rep["place"] = {"scale": float(s), "turn_deg": float(np.degrees(np.arccos(min(1, (np.trace(R) - 1) / 2)))),
                    "move_m": [float(x) for x in T], **st}
    rep["correspond"] = {"head_points_welded": int(len(HPw)), **info}
    return {"sim": sim, "Sub": cache["Sub"], "F2": cache["F2"], "U2": cache["U2"], "P2": Pp, "match": match,
            "head_quads": head_quads, "HPw": HPw, "head_rep": rep_, "head_uniq": uniq}


def run(spec, base, out, rep):
    A = Glb(os.path.join(REPO, spec["ref"]))
    t = time.time()
    pl = stage_place(base, A, rep)
    rep["timings_s"]["place"] = round(time.time() - t, 2)
    print(json.dumps(rep, indent=1))
    raise SystemExit("stop after place (dev)")
