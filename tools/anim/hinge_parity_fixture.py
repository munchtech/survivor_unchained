"""The fixture for godot/tests/HipHingeTests.cs: her hip hinges (helpers SPEC "hinges", drive_hinges) and her tasset
hinge (SPEC "tassets", drive_tassets) on every frame of
the four demo clips (idle_warden, run_warden, sword_heavy, leap), so Play/HipHinge.cs (HerJoints' copy) is checked
against it.

    python tools/anim/hinge_parity_fixture.py      # writes godot/tests/fixtures/hinge_parity.json

Her skeleton (tools/anim/data/heroine_skeleton.json, extend() adds the hinges). Per side: the parent's global rest
(rotation xyzw, position), the pivot, the hinge's local rest (rotation, position), the thigh's rest turn in the parent
(its local rotations composed down the chain); per frame the posed turn and the expected hinge local rotation."""
import json
import os
import sys
import types
from pathlib import Path

import numpy as np

import helpers as hp
from rig import REPO, Skeleton

OUT = REPO / "godot" / "tests" / "fixtures" / "hinge_parity.json"
CLIPS = ("idle_warden", "run_warden", "sword_heavy", "leap")


def clips_dir():
    for root in (os.environ.get("ANIM_OUT"), REPO / "tools" / "anim" / "out", REPO.parents[2] / "tools" / "anim" / "out"):
        if root and (Path(root) / "clips" / "run_warden.json").exists():
            return Path(root) / "clips"
    raise SystemExit("hinge_parity_fixture: no built clips (tools/anim/out/clips)")


def main():
    import skin
    sk = hp.extend(Skeleton.load())
    grot, gpos = sk.rest_globals()
    folder = clips_dir()
    out = {"spec": hp.SPEC["hinges"], "sides": []}
    for hg in hp.SPEC["hinges"]:
        for s in "lr":
            j = sk.index[hg["name"].replace("{s}", s)]
            p, b = sk.parent[j], sk.index[hg["bone"].replace("{s}", s)]
            side = {"name": sk.names[j], "left": s == "l", "amount": hg["amount"],
                    "parent_rot": grot[0, p].tolist(), "parent_pos": gpos[0, p].tolist(),
                    "pivot": hp.hinge_pivot(hg, s).tolist(), "rest_rot": sk.rest_rot[j].tolist(),
                    "rest_pos": sk.rest_pos[j].tolist(), "chain_rest": hp._below(sk, sk.rest_rot, p, b).tolist(), "frames": []}
            for cl in CLIPS:
                c = skin.Body.clip(types.SimpleNamespace(label="her", sk=sk), cl, folder)
                for f in range(c.rot.shape[0]):
                    rot = c.rot[f].copy()
                    hp.drive_hinges(sk, rot)
                    side["frames"].append({"clip": cl, "f": f, "chain": hp._below(sk, rot, p, b).tolist(), "hinge": rot[j].tolist()})
            out["sides"].append(side)
    # The tasset hinge (SPEC "tassets", drive_tassets): the parent's global rest, pivot, local rest, each thigh's rest
    # turn in the parent; per frame both thighs' posed turns and the expected local rotation.
    out["tasset_spec"] = hp.SPEC.get("tassets", [])
    out["tassets"] = []
    # (each entry of the spec; then the centred V again with roll on: roll 1.3, the hipv solver's suggestion, and a
    # harder 3.0 past the clamp, so the roll law is checked where the shipped roll is 0)
    variants = [(tg, tg) for tg in out["tasset_spec"]]
    base = next(t for t in out["tasset_spec"] if len(t["thighs"]) == 2)
    variants += [(base, {**base, "roll": r, "roll_from": f, "roll_soft": 6.0, "roll_max": m})
                 for r, f, m in ((1.3, 2.0, 20.0), (3.0, 0.0, 8.0))]
    for tg0, tg in variants:
        j = sk.index[tg["name"]]
        p = sk.parent[j]
        th = [sk.index[n] for n in tg["thighs"]]
        one = {"name": tg["name"], "amount": tg["amount"], "soft": tg["soft"],
               "roll": tg.get("roll", 0.0), "roll_from": tg.get("roll_from", 2.0), "roll_soft": tg.get("roll_soft", 6.0),
               "roll_max": tg.get("roll_max", 20.0), "sides": [1 if n.endswith("_l") else -1 for n in tg["thighs"]],
               "parent_rot": grot[0, p].tolist(), "parent_pos": gpos[0, p].tolist(), "pivot": list(tg["pivot"]),
               "rest_rot": sk.rest_rot[j].tolist(), "rest_pos": sk.rest_pos[j].tolist(),
               "chain_rest": [hp._below(sk, sk.rest_rot, p, b).tolist() for b in th], "frames": []}
        for cl in CLIPS:
            c = skin.Body.clip(types.SimpleNamespace(label="her", sk=sk), cl, folder)
            for f in range(c.rot.shape[0]):
                rot = c.rot[f].copy()
                sw, sp = hp.tasset_angles(sk, rot, tg)
                pitch, roll = hp.tasset_pose(tg, sw, sp)
                rot[j] = hp.qnorm(hp.qmul(sk.rest_rot[j], hp.tasset_q(pitch, roll)))
                one["frames"].append({"clip": cl, "f": f, "chains": [hp._below(sk, rot, p, b).tolist() for b in th],
                                      "tasset": rot[j].tolist(), "roll_deg": roll})
        out["tassets"].append(one)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(OUT, sum(len(x["frames"]) for x in out["sides"]), "hinge frames", sum(len(x["frames"]) for x in out["tassets"]),
          "tasset frames")


if __name__ == "__main__":
    main()
