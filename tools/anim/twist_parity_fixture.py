"""The fixture for godot/tests/ArmTwistTests.cs: her upper arm's twist chain (helpers SPEC "twist_chain") driven by
helpers.drive() frame to frame (unwrap state kept), so Play/ArmTwist.cs (HerJoints' math) is checked against it.

    python tools/anim/twist_parity_fixture.py      # writes godot/tests/fixtures/arm_twist_parity.json

Her skeleton (tools/anim/data/heroine_skeleton.json) with the chain added (extend(chain=True)); each side's upper
arm swung a little out and forward (below level, so the clavicle lift leaves it) and rolled through a sweep that
crosses +-180 (the unwrap) and runs out past unwrap_max (the one flip). Per frame: the upper arm's local pose as
drive() leaves it (what HerJoints reads), the unwrapped roll, each chain bone's local rotation and the shoulder
share's."""
import json

import numpy as np

import helpers as hp
from rig import REPO, Skeleton, qaxis, qinv, qmul, qnorm

OUT = REPO / "godot" / "tests" / "fixtures" / "arm_twist_parity.json"
SWEEP = {"r": [0, 40, 100, 150, 165, 172, 178, -178, -172, -165, -150, -120, -95, -85, -60, 0, 25],
         "l": [0, -60, -120, -170, -178, 176, 168, 150, 120, 95, 85, 30, 0, -10]}


def main():
    sk = hp.extend(Skeleton.load(), chain=True)
    I = sk.index
    tc = hp.SPEC["twist_chain"]
    chain = [n for n, _ in tc["nodes"] if "twist" in n]
    share = next(iter(tc["roll"]))
    nf = max(len(v) for v in SWEEP.values())
    state = {}
    frames = {s: [] for s in "lr"}
    for f in range(nf):
        rot = sk.rest_rot.copy()
        for s in "lr":
            u = I[f"upperarm_{s}"]
            roll = SWEEP[s][min(f, len(SWEEP[s]) - 1)]
            swing = qnorm(qmul(qaxis([1.0, 0, 0], 12.0), qaxis([0, 0, 1.0], -8.0 if s == "r" else 8.0)))
            rot[u] = qnorm(qmul(sk.rest_rot[u], qmul(swing, qaxis([0, 1.0, 0], roll))))
        rot = hp.drive(sk, rot, state=state, dt=1 / 30)
        for s in "lr":
            u = I[f"upperarm_{s}"]
            frames[s].append({"upper": list(rot[u]), "roll": state["roll:" + sk.names[u]],
                              "chain": {n.replace("{s}", s): list(rot[I[n.replace("{s}", s)]]) for n in chain},
                              "share": list(rot[I[share.replace("{s}", s)]])})
    sides = {}
    for s in "lr":
        u, j = I[f"upperarm_{s}"], I[share.replace("{s}", s)]
        hs = next(h for h in hp.SPEC["helpers"] if h["name"] == share)
        sides[s] = {"upper_rest": list(sk.rest_rot[u]), "share_own": list(qmul(qinv(sk.rest_rot[u]), sk.rest_rot[j])),
                    "share_amount": hs["amount"], "share_roll": tc["roll"][share],
                    "amounts": {n.replace("{s}", s): tc["amounts"].get(n, next(h for h in hp.SPEC["helpers"] if h["name"] == n)["amount"]) for n in chain},
                    "frames": frames[s]}
    OUT.write_text(json.dumps({"unwrap_max": tc["unwrap_max"], "sides": sides}, indent=1) + "\n")
    for s in "lr":
        print(s, "rolls", " ".join(f"{fr['roll']:.1f}" for fr in frames[s]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
