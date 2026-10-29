"""The fixture for godot/tests/ShoulderHelpersTests.cs: her shoulder helpers (helpers SPEC "shoulder") from
helpers.shoulder_helper on posed parents, so Play/ShoulderHelpers.cs (HerShoulder's math) is checked against it.

    python tools/anim/shoulder_parity_fixture.py      # writes godot/tests/fixtures/shoulder_parity.json

Her skeleton (tools/anim/data/heroine_skeleton.json) with the twist chain added (extend(chain=True)). Per helper and
case: A, its parent's and the upper arm's posed globals (their rest turned by seeded turns up to 70 degrees about
varied axes, origins moved a few cm), and the expected local pose under the parent (quaternion xyzw, scale, position:
rotation = inv(Rp) Rf, scale (sp, sa, sp) in its own axes, position = inv(Rp)(O - Op))."""
import json

import numpy as np

import helpers as hp
from rig import REPO, Skeleton, qaxis, qmatrix, qmul, qfrom_matrix

OUT = REPO / "godot" / "tests" / "fixtures" / "shoulder_parity.json"
AS = [0, 40, 59.9, 60, 75, 90, 110, 120, 140, 152, 161, 178]


def g4(q, p):
    G = np.eye(4)
    G[:3, :3] = qmatrix(q)
    G[:3, 3] = p
    return G


def posed(rng, G0):
    """G0 turned by a seeded turn (up to ~70 degrees, varied axis) about its own origin and moved a few cm."""
    ax = rng.normal(size=3)
    q = qaxis(ax / np.linalg.norm(ax), rng.uniform(0, 70))
    G = G0.copy()
    G[:3, :3] = qmatrix(q) @ G0[:3, :3]
    G[:3, 3] = G0[:3, 3] + rng.uniform(-0.04, 0.04, 3)
    return G


def quat(G):
    q = qfrom_matrix(G[:3, :3])
    return [float(v) for v in q]


def main():
    sk = hp.extend(Skeleton.load(), chain=True)
    I = sk.index
    grot, gpos = sk.rest_globals()
    Grest = {n: g4(grot[0][j], gpos[0][j]) for n, j in I.items()}
    frames = hp.shoulder_rest(Grest)
    rng = np.random.default_rng(7)
    out = {"a0": hp.SPEC["shoulder"]["A"][0], "a1": hp.SPEC["shoulder"]["A"][1], "bones": {}, "helpers": {}}
    for k, c in hp.SPEC["shoulder"]["bones"].items():
        out["bones"][k] = c
    worst = 0.0
    for n, f in frames.items():
        Gp0, Gon0 = Grest[f["parent"]], Grest[f["on"]]
        cases = []
        for A in AS:
            Mp, Mon = posed(rng, Gp0), posed(rng, Gon0)
            G = hp.shoulder_helper(f, A, Mp, Gp0, Mon, Gon0)
            Gl = np.linalg.inv(Mp) @ G          # local: rotation x scale, position, in the parent's posed frame
            R = Gl[:3, :3]
            sc = [float(np.linalg.norm(R[:, i])) for i in range(3)]
            Rl = R / np.array(sc)
            cases.append({"A": A, "Mp": [quat(Mp), list(Mp[:3, 3])], "Mon": [quat(Mon), list(Mon[:3, 3])],
                          "rot": quat(np.pad(Rl, ((0, 1), (0, 1)))), "scale": sc, "pos": list(Gl[:3, 3])})
            worst = max(worst, abs(np.linalg.det(Rl) - 1))
        out["helpers"][n] = {
            "kind": n[:-2], "side": f["s"], "parent": f["parent"], "on": f["on"],
            "Gp0": [quat(Gp0), list(Gp0[:3, 3])], "Gon0": [quat(Gon0), list(Gon0[:3, 3])],
            "G0": [quat(f["G0"]), list(f["G0"][:3, 3])],
            "upper0": list(Grest["upperarm_" + f["s"]][:3, 3]), "lower0": list(Grest["lowerarm_" + f["s"]][:3, 3]),
            "T0": None if f["T0"] is None else list(f["T0"]), "L0": f["L0"], "off": list(f["off"]), "cases": cases}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT, "det dev", worst)


if __name__ == "__main__":
    main()
