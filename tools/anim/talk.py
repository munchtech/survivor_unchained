"""A keyed talk laid over a standing clip (folk.py: a row's `talk="<clip name>"`; animation A1, 10 Nov).

The gestures are DATA: tools/anim/data/folk_talk.json, one entry per clip name, channels of keys
`[t seconds, value, ("still")]` through Marionette's keyed() curve (tools/motion/fit.py: a cubic Hermite, zero speed at
the first, the last and every "still" key). Every value is ADDED to the clip beneath (0 = the clip's own), so its
breath and sway carry on under the talk:

- `hand_l` / `hand_r` (metres): the wrist raised by this much above the clip's own wrist at that frame, by flexing the
  elbow alone about its own hinge (the upper arm's line is not touched: the elbow stays where the clip has it).
- `in_l` / `in_r` (degrees): the upper arm rolled about its own line, + = the forearm swings in toward his middle.
- `palm_l` / `palm_r` (degrees): the forearm rolled about its own line, + = the palm turns up (half in the forearm,
  half at the wrist, as retarget.spread_twist shares a take's).
- `wrist_l` / `wrist_r` (degrees): the hand turned on about the elbow's hinge, + = carrying on the forearm's rise.
- `nod` (+ = down), `turn` (+ = to his left), `tilt` (+ = toward his right shoulder), degrees at the Head joint.

Every channel must be 0 on the first and the last frame (no gesture straddles a loop's seam): lay() refuses otherwise.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np

from rig import DATA, Skeleton, qaxis, qinv, qmul, qrot

SPECS = DATA / "folk_talk.json"
ARM = ("hand", "in", "palm", "wrist")
HEAD = ("nod", "turn", "tilt")
CHANNELS = tuple(f"{c}_{s}" for c in ARM for s in "lr") + HEAD


def keyed_curve():
    """Marionette's keyed() (tools/motion/fit.py), loaded as a package of its own name: tools/anim has a motion.py,
    so `from motion import fit` would find that instead. MARIONETTE_DIR as p4.py's."""
    name = "marionette_motion"
    if name not in sys.modules:
        d = Path(os.environ.get("MARIONETTE_DIR", "C:/Users/munch/Desktop/Marionette_motion")) / "tools" / "motion"
        if not (d / "fit.py").exists():
            raise SystemExit(f"talk.py: Marionette's motion core is not at {d} (set MARIONETTE_DIR)")
        spec = importlib.util.spec_from_file_location(name, d / "__init__.py", submodule_search_locations=[str(d)])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return importlib.import_module(name + ".fit").keyed


def spec_of(name, path=SPECS):
    return json.loads(Path(path).read_text())[name]


def _unit(v):
    return v / np.linalg.norm(v)


def lay(sk: Skeleton, local, pos, spec, fps=30.0):
    """The clip's locals with the spec's keyed talk laid over them, and a line for the clip's "changes". A spec with
    no keys returns the locals as they came."""
    chans = {k: spec[k] for k in CHANNELS if spec.get(k)}
    if not chans:
        return local, ""
    keyed = keyed_curve()
    T = local.shape[0]
    val = {k: keyed([list(x) for x in v], T, fps)[:, 0] for k, v in chans.items()}
    for k, v in val.items():
        if max(float(x[0]) for x in chans[k]) > (T - 1) / fps + 1e-9:
            raise SystemExit(f"talk: {k} has a key after the clip's end ({(T - 1) / fps:.2f} s)")
        if abs(v[0]) > 1e-9 or abs(v[-1]) > 1e-9:
            raise SystemExit(f"talk: {k} is not 0 on the first and the last frame (a gesture would straddle the seam)")
    zero = np.zeros(T)
    g, p = sk.fk(local, pos)
    rg = sk.rest_globals()[0][0]
    L = local.copy()
    chest = sk.i("spine_03")
    for side in "lr":
        rise, roll_in, palm, wrist = (val.get(f"{c}_{side}", zero) for c in ARM)
        if not any(f"{c}_{side}" in val for c in ARM):
            continue
        ua, la, ha = (sk.i(f"{b}_{side}") for b in ("upperarm", "lowerarm", "hand"))
        s = 1.0 if side == "l" else -1.0
        for f in range(T):
            if rise[f] == 0 and roll_in[f] == 0 and palm[f] == 0 and wrist[f] == 0:
                continue
            pu, pe, pw = p[f, ua], p[f, la], p[f, ha]
            u = _unit(pe - pu)
            fwd = qrot(qmul(g[f, chest], qinv(rg[chest])), [0, 0, 1.0])
            # The upper arm rolled about its own line: the elbow stays, the forearm swings in.
            r_up = qaxis(u, s * roll_in[f])
            gu, gl, gh = qmul(r_up, g[f, ua]), qmul(r_up, g[f, la]), qmul(r_up, g[f, ha])
            fore = qrot(r_up, pw - pe)
            length = float(np.linalg.norm(fore))
            fd = fore / length
            # The elbow's hinge: square to the upper arm and the forearm (a little of the forward flex's own axis
            # mixed in, so a straight arm has one too); + about it flexes.
            hinge = _unit(np.cross(u, fd) + 0.02 * _unit(np.cross(u, fwd)))
            gd = np.cross(hinge, fd)
            # The wrist's height through the flex is R cos(theta - phi): the flex that puts it `rise` above the
            # clip's own wrist (as near as the forearm reaches).
            R, phi = float(np.hypot(fd[1], gd[1])), float(np.arctan2(gd[1], fd[1]))
            want = (pw[1] + rise[f] - pe[1]) / length
            theta = phi - float(np.arccos(np.clip(want / R, -1, 1)))
            if gd[1] <= 0:
                # (A forearm hanging back of plumb: the flex is counted from the mirrored height in front.)
                theta -= phi - float(np.arccos(np.clip(fd[1] / R, -1, 1)))
            r_fl = qaxis(hinge, np.degrees(theta))
            gl, gh = qmul(r_fl, gl), qmul(qmul(qaxis(hinge, wrist[f]), r_fl), gh)
            fd2 = qrot(r_fl, fd)
            gl = qmul(qaxis(fd2, -s * palm[f] / 2), gl)
            gh = qmul(qaxis(fd2, -s * palm[f]), gh)
            if roll_in[f] != 0:
                L[f, ua] = qmul(qinv(g[f, sk.parent[ua]]), gu)
            L[f, la] = qmul(qinv(gu), gl)
            L[f, ha] = qmul(qinv(gl), gh)
    if any(k in val for k in HEAD):
        hd = sk.i("Head")
        ax = [_unit(qrot(qinv(rg[hd]), a)) for a in ([1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0])]
        nod, turn, tilt = (val.get(k, zero) for k in HEAD)
        for f in range(T):
            if nod[f] == 0 and turn[f] == 0 and tilt[f] == 0:
                continue
            q = qmul(qmul(qaxis(ax[1], turn[f]), qaxis(ax[0], nod[f])), qaxis(ax[2], tilt[f]))
            L[f, hd] = qmul(local[f, hd], q)
    said = []
    for side, word in (("r", "right"), ("l", "left")):
        if f"hand_{side}" in val:
            v = val[f"hand_{side}"]
            said.append(f"the {word} hand raised to {v.max() * 100:.0f} cm above its hang")
    line = ("; a keyed talk laid over it (tools/anim/data/folk_talk.json: " + ", ".join(said or ["the head only"]) +
            (f", the head nodding to {val['nod'].max():.0f} degrees" if "nod" in val else "") +
            "; the upper arms' lines, the trunk and the legs as the clip has them)")
    return L, line
