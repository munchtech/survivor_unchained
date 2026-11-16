"""The fixture for godot/tests/HipHingeTests.cs: her hip hinges (helpers SPEC "hinges", drive_hinges) on every frame of
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(OUT, sum(len(x["frames"]) for x in out["sides"]), "frames")


if __name__ == "__main__":
    main()
