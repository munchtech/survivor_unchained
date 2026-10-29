"""The fixture for godot/tests/ElbowHingeTests.cs: her elbow share and point (helpers SPEC "hinge": true) driven by
helpers.drive(), so Play/ElbowHinge.cs (HerJoints' math) is checked against it.

    python tools/anim/elbow_parity_fixture.py      # writes godot/tests/fixtures/elbow_hinge_parity.json

Her skeleton with the chain (extend(chain=True)); per side ~20 forearm poses, bends 0..150 deg about the share's X,
axes tilted 15-30 deg toward the forearm's +Y and its Z, and some roll about +Y. Per frame: the forearm's local pose
as drive() leaves it (what HerJoints reads) and each hinged helper's local rotation. Asserts one frame where the old
slerp result differs from the hinge result by more than 5 deg."""
import json
import math

import numpy as np

import helpers as hp
from rig import REPO, Skeleton, qaxis, qinv, qmul, qnorm, qrot

OUT = REPO / "godot" / "tests" / "fixtures" / "elbow_hinge_parity.json"


def apart_deg(a, b):
    d = qmul(qinv(a), b)
    return 2 * math.degrees(math.atan2(float(np.linalg.norm(d[:3])), abs(float(d[3]))))


def main():
    sk = hp.extend(Skeleton.load(), chain=True)
    I = sk.index
    hinged = [h for h in hp.SPEC["helpers"] if h.get("hinge")]
    out = {"sides": {}}
    biggest = 0.0
    for s in "lr":
        la = I[f"lowerarm_{s}"]
        share = I[f"lowerarm_share_{s}"]
        x = qrot(qmul(qinv(sk.rest_rot[la]), sk.rest_rot[share]), [1.0, 0, 0])
        bends = [0, 20, 45, 70, 90, 110, 130, 150]
        poses = []
        for b in bends:
            poses.append((x, b, 0))
        for tilt in (15, 30):
            for tgt in ([0, 1.0, 0], [0, 0, 1.0]):
                t = np.array(tgt) * math.sin(math.radians(tilt)) + x * math.cos(math.radians(tilt))
                for b in (60, 120, 150):
                    poses.append((t / np.linalg.norm(t), b, 0))
        for b, roll in ((90, 40), (120, -70), (140, 120)):
            poses.append((x, b, roll))
        frames = []
        for axis, b, roll in poses:
            rot = sk.rest_rot.copy()
            rot[la] = qnorm(qmul(sk.rest_rot[la], qmul(qaxis(axis, b), qaxis([0, 1.0, 0], roll))))
            rot = hp.drive(sk, rot)
            pose = rot[la].copy()
            fr = {"pose": list(pose), "helpers": {}}
            swing, _, _ = hp._twist_y(qmul(qinv(sk.rest_rot[la]), pose))
            for h in hinged:
                j = I[h["name"].replace("{s}", s)]
                fr["helpers"][h["name"].replace("{s}", s)] = list(rot[j])
                own = qmul(qinv(sk.rest_rot[la]), sk.rest_rot[j])
                old = qnorm(qmul(sk.rest_rot[la], qmul(hp.qslerp(np.array([0, 0, 0, 1.0]), swing, h["amount"]), own)))
                biggest = max(biggest, apart_deg(old, rot[j]))
            frames.append(fr)
        side = {"rest": list(sk.rest_rot[la]), "helpers": {}, "frames": frames}
        for h in hinged:
            j = I[h["name"].replace("{s}", s)]
            side["helpers"][h["name"].replace("{s}", s)] = {
                "own": list(qmul(qinv(sk.rest_rot[la]), sk.rest_rot[j])), "amount": h["amount"]}
        out["sides"][s] = side
    assert biggest > 5.0, f"no frame where the old slerp differs from the hinge by > 5 deg ({biggest:.2f})"
    out["max_old_vs_new_deg"] = biggest
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print("max old-vs-new deg", round(biggest, 2), "frames", len(frames), "wrote", OUT)


if __name__ == "__main__":
    main()
