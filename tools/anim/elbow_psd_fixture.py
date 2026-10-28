"""Writes godot/tests/fixtures/elbow_psd_parity.json (Body 19): her forearm posed flexed -20..160 deg, swung sideways
and rolled; helpers.flexion and the elbow_psd correctives' weights (helpers.corrective_weight) per pose, for
ElbowPsdTests (Play/ElbowPsd, the game's twin).    python tools/anim/elbow_psd_fixture.py"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import helpers as hp  # noqa: E402
from rig import Skeleton, qaxis, qbetween, qmul  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sk = Skeleton.load(ROOT / "tools" / "anim" / "data" / "heroine_skeleton.json")
rng = np.random.default_rng(19)
cs = [c for c in hp.SPEC["correctives"] if c.get("on") == "flex"]
out = {"shapes": [c["name"] for c in cs], "sides": {}}
for s in "lr":
    j = sk.index[f"lowerarm_{s}"]
    frames = []
    for k in range(40):
        fl = -20 + 180 * k / 39 + rng.uniform(-2, 2)
        dv = rng.uniform(-20, 20)
        roll = rng.uniform(-90, 90)
        want = [math.sin(math.radians(dv)), math.cos(math.radians(dv)) * math.cos(math.radians(fl)),
                math.cos(math.radians(dv)) * math.sin(math.radians(fl))]
        q = qmul(sk.rest_rot[j], qmul(qbetween([0, 1.0, 0], want), qaxis([0, 1.0, 0], roll)))
        rot = sk.rest_rot.copy()
        rot[j] = q
        f = hp.flexion(sk, rot, f"lowerarm_{s}")
        frames.append({"pose": [float(x) for x in q], "flex": f, "w": [hp.corrective_weight(c, f) for c in cs]})
    out["sides"][s] = {"rest": [float(x) for x in sk.rest_rot[j]], "frames": frames}
p = ROOT / "godot" / "tests" / "fixtures" / "elbow_psd_parity.json"
p.write_text(json.dumps(out, indent=0) + "\n")
print("wrote", p)
