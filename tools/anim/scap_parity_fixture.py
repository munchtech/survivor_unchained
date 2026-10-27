"""The fixture for godot/tests/ScapRotationTests.cs: her scapulae (helpers SPEC "scap") driven by helpers.drive() on
poses whose upper arms sweep from hanging to overhead, so Play/ScapRotation.cs (HerScap's math) is checked against it.

    python tools/anim/scap_parity_fixture.py      # writes godot/tests/fixtures/scap_parity.json

Her skeleton (tools/anim/data/heroine_skeleton.json) with the twist chain and the scapulae added (extend(chain=True),
add_scap). Per frame and side: the pelvis, neck_01, upper arm and forearm origins as drive() leaves them (what HerScap
reads: after the clavicle lift), A, the scapula's angle and its local rotation."""
import json

import numpy as np

import helpers as hp
from rig import REPO, Skeleton, qaxis, qmul, qnorm

OUT = REPO / "godot" / "tests" / "fixtures" / "scap_parity.json"
# (abduction about her front, flexion about her side) in degrees, per frame; the right side its own sweep
SWEEP = {"l": [(0, 0), (20, 5), (35, 0), (45, 10), (60, 0), (90, 0), (100, 30), (115, 0), (140, 10), (150, 0), (160, -5), (175, 0)],
         "r": [(5, 0), (30, 0), (40, 20), (55, 0), (80, 40), (120, 0), (135, 0), (148, 15), (155, 0), (170, 0), (10, 60), (0, 90)]}


def main():
    sk = hp.add_scap(hp.extend(Skeleton.load(), chain=True))
    I = sk.index
    g0 = sk.rest_globals()[0][0]
    out = {"per_deg": hp.SPEC["scap"]["per_deg"], "from": hp.SPEC["scap"]["from"], "ease": hp.SPEC["scap"]["ease"],
           "axis": hp.SPEC["scap"]["axis"], "sides": {}}
    frames = {s: [] for s in "lr"}
    state = {}
    for f in range(len(SWEEP["l"])):
        rot = sk.rest_rot.copy()
        for s in "lr":
            u = I[f"upperarm_{s}"]
            ab, fl = SWEEP[s][f]
            sg = 1.0 if s == "l" else -1.0
            # in the upper arm's parent's frame turned as her torso is at rest: a turn about her front (abduction,
            # from her rest A-pose's own hang) and about her side (flexion)
            gp = sk.fk(rot[None])[0][0][sk.parent[u]]
            from rig import qinv, qrot
            fwd, lat = qrot(qinv(gp), [0, 0, 1.0]), qrot(qinv(gp), [sg, 0, 0])
            turn = qmul(qaxis(fwd, sg * (ab - 40.0)), qaxis(lat, -sg * fl))
            rot[u] = qnorm(qmul(turn, sk.rest_rot[u]))
        rep = {}
        rot = hp.drive(sk, rot, state=state, dt=1 / 30)
        grot, gpos = sk.fk(rot[None])
        gpos = gpos[0]
        hp.scap(sk, rot.copy(), rep)
        for s in "lr":
            j = I[f"scap_{s}"]
            frames[s].append({"pelvis": list(gpos[I["pelvis"]]), "neck": list(gpos[I["neck_01"]]),
                              "upper": list(gpos[I[f"upperarm_{s}"]]), "lower": list(gpos[I[f"lowerarm_{s}"]]),
                              "A": rep[s][0], "deg": rep[s][1], "scap": list(rot[j])})
    for s in "lr":
        j = I[f"scap_{s}"]
        out["sides"][s] = {"rest": list(sk.rest_rot[j]), "global_rest": list(g0[j]), "frames": frames[s]}
        print(s, " ".join(f"{fr['A']:.0f}:{fr['deg']:.1f}" for fr in frames[s]))
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
