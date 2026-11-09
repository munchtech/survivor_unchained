"""The C# corrective/helper driver's parity fixture (P1 F): rig_drive.drive on sampled poses of the published B.

    python tools/body/p1_rig_fixture.py [godot/art/people/body_p1]   -> godot/tests/fixtures/p1_rig_parity.json
    python tools/body/p1_rig_fixture.py PUB --hand DUMP --out FILE     (P1 R1 sliders: a body with rig.json "hand_clear"
        (a slider variant's published folder); the poses also take frames of its baked idles from the keys dump DUMP
        (clipcheck's), hands by and on her thighs, so the hand-clearance law is held where it acts)

Writes B's close skeleton (names, parents, rest worlds), the rig it drove (the published rig.json, plus three test
rows: an "rbf" on the thigh's direction with its solved M, an "arc" along the hip's flexion and a legacy row, each with
"test_" shapes, so every law the port carries is checked even before the build ships them), and for each sampled pose
the input bone worlds G (core bones turned in their parents' frames, helpers carried at rest), the driven worlds and
the weights. godot/tests/P1RigTests.cs holds the C# port (godot/logic/Play/P1Rig.cs) to them within 1e-6 m / 1e-3.
Derivation: (c) inherited: tools/body/rig_drive.py is the reference (rig.json "poser"); the poses are fixed by seed.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gl import Glb  # noqa: E402
import rig_drive as rd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))


def rot(axis, deg):
    return rd._expm(rd._n(np.asarray(axis, float)) * math.radians(deg))


def fk(sk, local):
    """Bone worlds from per-bone local turns (3x3, in the bone's rest frame; missing = rest)."""
    G = np.zeros_like(sk.rest)
    for j in range(len(sk.names)):          # joints are parent-first in the file's skin order (checked)
        p = sk.parent[j]
        L = sk.rest[j] if p < 0 else np.linalg.inv(sk.rest[p]) @ sk.rest[j]
        R = np.eye(4)
        if j in local:
            R[:3, :3] = local[j]
        G[j] = (np.eye(4) if p < 0 else G[p]) @ L @ R
    return G


def from_dump(sk, rig, dump, clip, frames):
    """Bone worlds (glb space) of a baked clip's frames as clipcheck.Body.pose lays them before the laws: the dump's
    globals, bones it lacks and unkeyed helpers carried at rest local."""
    d = json.load(open(os.path.join(dump, f"{clip}.json")))
    names = d["b_names"]
    mats = lambda a: np.concatenate([np.asarray(a, float).reshape(-1, 3, 4), np.tile([[[0, 0, 0, 1.0]]], (len(a), 1, 1))], 1)
    rest_d = mats(d["b_rest"])
    X = sk.rest[sk.index["pelvis"]] @ np.linalg.inv(rest_d[names.index("pelvis")])
    helpers = {h["name"].replace("{s}", s) for h in rig.get("helpers", []) for s in ("l", "r")}
    keyed = set(d["keyed"])
    out = {}
    for f in frames:
        Gd = mats(d["B"][f])
        G = sk.rest.copy()
        got = np.zeros(len(G), bool)
        for a, n in enumerate(names):
            k = sk.index.get(n, -1)
            if k >= 0:
                G[k] = X @ Gd[a]
                got[k] = True
        for k in range(len(sk.names)):          # parent-first (checked)
            pk = sk.parent[k]
            if pk >= 0 and (not got[k] or sk.names[k] in helpers and sk.names[k] not in keyed):
                G[k] = G[pk] @ (np.linalg.inv(sk.rest[pk]) @ sk.rest[k])
        out[f"{clip}_{f}"] = G
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hand = sys.argv[sys.argv.index("--hand") + 1] if "--hand" in sys.argv else None
    dst = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    args = [a for a in args if a not in (hand, dst)]
    pub = args[0] if args else os.path.join(ROOT, "godot", "art", "people", "body_p1")
    sk = Glb(os.path.join(pub, "body.glb")).skeleton()
    assert all(sk.parent[j] < j for j in range(len(sk.names))), "joints not parent-first"
    rig = json.load(open(os.path.join(pub, "rig.json")))
    I = sk.index
    # the extra rows: every law the port carries
    d0 = lambda b, e: rd._n(sk.rest[I[e]][:3, 3] - sk.rest[I[b]][:3, 3])
    up = {s: d0(f"thigh_{s}", f"calf_{s}") for s in "lr"}
    keys = {s: [up[s].tolist()] + [rd._n(rot([1, 0, 0], -a) @ up[s]).tolist() for a in (45, 90)]
            + [rd._n(rot([0, 0, 1], (1 if s == "l" else -1) * 40) @ up[s]).tolist()] for s in "lr"}
    keys_p = {s: (np.asarray(keys[s]) @ np.eye(3)).tolist() for s in "lr"}      # in the pelvis' rest-aligned frame
    rbf = {"joint": "test_hip", "law": "rbf", "bone": "thigh_{s}", "end": "calf_{s}", "frame": "pelvis",
           "sigma_deg": 40.0, "keys": keys_p, "shapes": ["test_flex45_{s}", "test_flex90_{s}", "test_abd40_{s}"]}
    rbf["M"] = {s: rd.rbf_solve(keys_p[s], rbf["sigma_deg"]).tolist() for s in "lr"}
    arc_k = {s: [up[s].tolist()] + [rd._n(rot([1, 0, 0], -a) @ up[s]).tolist() for a in (15, 30, 45, 60, 75, 90)]
             for s in "lr"}
    arc = {"joint": "test_arc", "law": "arc", "bone": "thigh_{s}", "end": "calf_{s}", "frame": "pelvis",
           "keys": arc_k, "gate_deg": [10.0, 25.0], "shapes": [f"test_arc{a}_{{s}}" for a in (15, 30, 45, 60, 75, 90)]}
    legacy = {"name": "test_legacy_{s}", "bone": "lowerarm_{s}", "on": "angle", "keys": [10.0, 60.0, 120.0]}
    rig = dict(rig)
    rig["correctives"] = list(rig["correctives"]) + [rbf, arc, legacy]
    rng = np.random.default_rng(7)
    core = [n for n in sk.names if not any(n == h["name"].replace("{s}", s) for h in rig["helpers"] for s in "lr")]
    poses = {
        "rest": {},
        "elbows90_knees60": {I["lowerarm_l"]: rot([1, 0, 0], 90), I["lowerarm_r"]: rot([1, 0, 0], 90),
                             I["calf_l"]: rot([1, 0, 0], 60), I["calf_r"]: rot([1, 0, 0], 60)},
        "arm_up_twist": {I["upperarm_l"]: rot([0, 0, 1], -80), I["hand_l"]: rot([0, 1, 0], 60),
                         I["upperarm_r"]: rot([1, 0, 1], 70), I["lowerarm_r"]: rot([0, 1, 0], -50)},
        # the hanging branch (A below the rest's ~43): both upper arms turned down toward the torso, one reaching
        # forward (protraction and glide)
        "arms_hang": {I["upperarm_l"]: rot([0, 0, 1], -38), I["upperarm_r"]: rot([0, 0, 1], 30) @ rot([1, 0, 0], 25)},
        # the retraction-by-plane fade (elevation past 95): her left raised forward (flexion, reach), her right
        # raised out to the side (abduction)
        "arms_raised": {I["upperarm_l"]: rot([1, 0, 0], 100) @ rot([0, 0, 1], 60), I["upperarm_r"]: rot([0, 0, 1], -62) @ rot([1, 0, 0], 30)},
        "hips": {I["thigh_l"]: rot([1, 0, 0], -50), I["thigh_r"]: rot([0, 0, 1], 25), I["calf_l"]: rot([1, 0, 0], 100),
                 I["foot_r"]: rot([0, 1, 0], 40)},
    }
    for k in range(4):
        poses[f"random_{k}"] = {I[n]: rot(rng.normal(size=3), float(rng.uniform(0, 45))) for n in core
                                if n not in ("root",)}
    dumped = {}
    if hand:
        assert "hand_clear" in rig, f"{pub}/rig.json has no hand_clear"
        for clip, fr in (("idle_reaver_look", (0, 45, 95)), ("idle_reaver_town", (0, 60)), ("run_warden", (5, 20))):
            dumped.update(from_dump(sk, rig, hand, clip, fr))
    out = {"why": __doc__.split("\n")[0], "names": sk.names, "parent": [int(p) for p in sk.parent],
           "rest": [m.tolist() for m in sk.rest], "rig": rig, "poses": []}
    for name, loc in list(poses.items()) + list(dumped.items()):
        G = loc if isinstance(loc, np.ndarray) else fk(sk, loc)
        G2, w = rd.drive(sk, G, rig)
        if name == "rest":      # the rest is exactly neutral (the girdle's tables are relative to the rest)
            assert np.abs(G2 - G).max() < 1e-9, f"rest not identity: {np.abs(G2 - G).max()}"
        out["poses"].append({"name": name, "G": [m.tolist() for m in G], "driven": [m.tolist() for m in G2],
                             "weights": w})
        print(name, "max weight", max(w.values()) if w else 0, {k: round(v, 3) for k, v in w.items() if v > 0.01})
    dst = dst or os.path.join(ROOT, "godot", "tests", "fixtures", "p1_rig_parity.json")
    with open(dst, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", os.path.relpath(dst, ROOT), os.path.getsize(dst) // 1024, "KB")


if __name__ == "__main__":
    main()
