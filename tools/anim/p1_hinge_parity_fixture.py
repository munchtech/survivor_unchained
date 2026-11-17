"""The fixture for godot/tests/P1HingeTests.cs: body B's (P1Laws) hip hinges and tasset hinge, from helpers.py with
B's skeleton (tools/anim/data/body_p1_skeleton.json; extend() adds the three bones, pivots moved with their "at" bone),
on B's clips idle_warden, run_warden, sword_heavy, leap.

    python tools/anim/p1_hinge_parity_fixture.py [--clips DIR]    # writes godot/tests/fixtures/p1_hinge_parity.json

Clips are read from --clips (default tools/anim/data/body_p1/clips). If they are missing, synthetic poses stand in
(40 frames per clip name, random thigh rotations within +-70 deg about random axes, seed 1) and "source" says so.
Same per-side fields as hinge_parity.json, plus the B-resolved pivots. If A's built clips exist too, prints per hinge the
max |A hinge_angle - B hinge_angle| over the same clip and frame index (report only)."""
import json
import math
import sys
import types
from pathlib import Path

import numpy as np

import helpers as hp
from rig import REPO, Skeleton

OUT = REPO / "godot" / "tests" / "fixtures" / "p1_hinge_parity.json"
CLIPS = ("idle_warden", "run_warden", "sword_heavy", "leap")


def a_clips():
    import os
    for root in (os.environ.get("ANIM_OUT"), REPO / "tools" / "anim" / "out", REPO.parents[2] / "tools" / "anim" / "out"):
        if root and (Path(root) / "clips" / "run_warden.json").exists():
            return Path(root) / "clips"
    return None


def synthetic(sk, name, n=40):
    rng = np.random.default_rng(1 + CLIPS.index(name))
    frames = []
    for _ in range(n):
        rot = np.array(sk.rest_rot, float).copy()
        for t in ("thigh_l", "thigh_r"):
            ax = rng.normal(size=3)
            ax /= np.linalg.norm(ax)
            rot[sk.index[t]] = hp.qnorm(hp.qmul(sk.rest_rot[sk.index[t]], hp.qaxis(ax, rng.uniform(-70, 70))))
        frames.append(rot)
    return frames


def main():
    folder = Path(sys.argv[sys.argv.index("--clips") + 1]) if "--clips" in sys.argv else REPO / "tools" / "anim" / "data" / "body_p1" / "clips"
    base = Skeleton.load(REPO / "tools" / "anim" / "data" / "body_p1_skeleton.json")
    sk = hp.extend(base)
    grot, gpos = sk.rest_globals()
    real = all((folder / f"{c}.json").exists() for c in CLIPS)
    if real:
        import skin

    def poses(cl):
        if real:
            c = skin.Body.clip(types.SimpleNamespace(label="her", sk=sk), cl, folder)
            return [c.rot[f].copy() for f in range(c.rot.shape[0])]
        return synthetic(sk, cl)

    clip_poses = {cl: poses(cl) for cl in CLIPS}
    out = {"source": f"clips {folder}" if real else "synthetic: 40 frames per clip name, thigh +-70 deg random axes, seed 1+index",
           "body": "p1", "spec": hp.SPEC["hinges"], "sides": []}
    angles = {}
    for hg in hp.SPEC["hinges"]:
        for s in "lr":
            j = sk.index[hg["name"].replace("{s}", s)]
            p, b = sk.parent[j], sk.index[hg["bone"].replace("{s}", s)]
            side = {"name": sk.names[j], "left": s == "l", "amount": hg["amount"],
                    "parent_rot": grot[0, p].tolist(), "parent_pos": gpos[0, p].tolist(),
                    "pivot": hp.hinge_pivot(hg, s, sk).tolist(), "rest_rot": sk.rest_rot[j].tolist(),
                    "rest_pos": sk.rest_pos[j].tolist(), "chain_rest": hp._below(sk, sk.rest_rot, p, b).tolist(), "frames": []}
            for cl in CLIPS:
                for f, rot0 in enumerate(clip_poses[cl]):
                    rot = rot0.copy()
                    hp.drive_hinges(sk, rot)
                    angles[(sk.names[j], cl, f)] = hp.hinge_angle(sk, rot, sk.names[j])
                    side["frames"].append({"clip": cl, "f": f, "chain": hp._below(sk, rot, p, b).tolist(), "hinge": rot[j].tolist()})
            out["sides"].append(side)
    out["tasset_spec"] = hp.SPEC.get("tassets", [])
    out["tassets"] = []
    for tg in out["tasset_spec"]:
        j = sk.index[tg["name"]]
        p = sk.parent[j]
        th = [sk.index[n] for n in tg["thighs"]]
        one = {"name": tg["name"], "amount": tg["amount"], "soft": tg["soft"],
               "parent_rot": grot[0, p].tolist(), "parent_pos": gpos[0, p].tolist(),
               "pivot": hp.tasset_pivot(tg, sk).tolist(),
               "rest_rot": sk.rest_rot[j].tolist(), "rest_pos": sk.rest_pos[j].tolist(),
               "chain_rest": [hp._below(sk, sk.rest_rot, p, b).tolist() for b in th], "frames": []}
        for cl in CLIPS:
            for f, rot0 in enumerate(clip_poses[cl]):
                rot = rot0.copy()
                hp.drive_tassets(sk, rot)
                angles[(sk.names[j], cl, f)] = hp.hinge_angle(sk, rot, sk.names[j])
                one["frames"].append({"clip": cl, "f": f, "chains": [hp._below(sk, rot, p, b).tolist() for b in th],
                                      "tasset": rot[j].tolist()})
        out["tassets"].append(one)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(OUT, out["source"], sum(len(x["frames"]) for x in out["sides"]), "hinge frames")
    ad = a_clips()
    if ad is not None and real:
        import skin
        ska = hp.extend(Skeleton.load())
        worst = {}
        for cl in CLIPS:
            c = skin.Body.clip(types.SimpleNamespace(label="her", sk=ska), cl, ad)
            for f in range(min(c.rot.shape[0], len(clip_poses[cl]))):
                rot = c.rot[f].copy()
                hp.drive_hinges(ska, rot)
                hp.drive_tassets(ska, rot)
                for n in {k[0] for k in angles}:
                    d = abs(hp.hinge_angle(ska, rot, n) - angles[(n, cl, f)])
                    worst[n] = max(worst.get(n, 0.0), d)
        for n, d in sorted(worst.items()):
            print(f"A vs B max |hinge angle diff| {n}: {d:.3f} deg")
    else:
        print("A-vs-B angle report skipped (needs both B clips and A's built clips)")


if __name__ == "__main__":
    main()
