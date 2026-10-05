"""Her faces to start from, fitted to their reference paintings
(face_refs.py) by her own sliders: MediaPipe's landmarks read off each
view of a reference, and the slider settings found that best move the same
points of her face (face_lab.py's anchors, read off her own face at several
turns) onto them. So a preset is a slider setting, and the player carries on
from it.

Runs in face_fit.py's Python (MediaPipe):

    <py> tools/assets/face_presets.py targets <targets.json>
    <py> tools/assets/face_presets.py fit <a_0.npz,a_20.npz,...> <out.json> name=ref.png ... [--reg 12]
    <py> tools/assets/face_presets.py presets <fits.json> <her_fits.json> <out.json> [--k 1.6] preset=ref ...
    <py> tools/assets/face_presets.py lab <fits.json> <faces.json>

targets: every target her sliders are made of (face_lab.py anchors them).
fit: each reference's sliders, -1 to 1 (both views of it, each matched to
the anchors seen nearest its own turn), written as {name: {slider: v}}.
presets: each preset from its chosen reference's fit, less what her own
references' fits share (the difference between a painting and a render),
drawn out k times.
lab: those as target weights over her face, for face_lab.py to render.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_fit as ff  # noqa: E402
import face_shapes as fs  # noqa: E402

# Sliders the landmarks of two views from in front cannot judge (they move
# her face toward or away from the camera, or are her ears): held at her
# own, to be set by eye in profile.
HELD = ("nose_projection", "lips_forward", "chin_forward", "jaw_forward", "eyes_depth", "brow_ridge", "cheekbone_prominence",
        "forehead_slope", "forehead_round", "ears_size", "ears_pointed", "ears_out", "ears_lobes")


def keyed():
    """Her sliders made as keys (not her bones'), in order."""
    return [s for s in fs.SLIDERS if s not in fs.BONE_SLIDERS]


def all_targets():
    out = []
    for s in keyed():
        for side in fs.slider_keys(s):
            for t in side:
                if t not in out:
                    out.append(t)
    return out


def slider_columns(raw):
    """An anchor set's moves per slider side (s+ and s-), from its targets'."""
    names = [str(t) for t in raw["targets"]]
    D = raw["D"]
    cols, ids = [], []
    for s in keyed():
        for sign, side in zip("+-", fs.slider_keys(s)):
            cols.append(sum(w * D[names.index(t)] for t, w in side.items()))
            ids.append(s + sign)
    return dict(raw, D=np.array(cols, np.float32), targets=np.array(ids))


def to_targets(sliders):
    """Slider settings as target weights (face_lab.py's faces)."""
    out = {}
    for s, v in sliders.items():
        if s not in fs.SLIDERS or s in fs.BONE_SLIDERS or abs(v) < 1e-4:
            continue
        side = fs.slider_keys(s)[0 if v > 0 else 1]
        for t, w in side.items():
            out[t] = round(out.get(t, 0.0) + w * abs(v), 4)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "targets":
        json.dump(all_targets(), open(a[1], "w"), indent=0)
        print(len(all_targets()), "targets")
    elif a[0] == "fit":
        names = a[1].split(",")
        sets = [ff.prepared(slider_columns(dict(np.load(p)))) for p in names]
        ids = [s + sign for s in keyed() for sign in "+-"]
        reg = float(a[a.index("--reg") + 1]) if "--reg" in a else 12.0
        out, errs = {}, {}
        for arg in a[3:]:
            if "=" not in arg:
                continue
            name, ref = arg.split("=", 1)
            marks = []
            for part in ("left", "right"):
                img, _ = ff.load(ref, part)
                L = ff.detect(img)
                if L is None:
                    raise SystemExit(f"no face in the {part} of {ref}")
                marks.append(L)
            views = [(sets[0], marks[0])]
            k = 1 + ff.match(sets[1:], marks[1]) if len(sets) > 1 else 0
            views.append((sets[k], marks[1]))
            keep = [i for i in ids if i[:-1] in HELD]
            w, err, yaw = ff.fit(views, ids, reg=reg, keep=keep)
            v = {}
            for s in keyed():
                x = w.get(s + "+", 0.0) - w.get(s + "-", 0.0)
                if abs(x) >= 0.02:
                    v[s] = round(float(np.clip(x, -1, 1)), 2)
            out[name] = v
            errs[name] = [round(e, 2) for e in err]
            print("FIT", name, "error %s mm, turned %s deg:" % (errs[name], [round(y) for y in yaw]), json.dumps(v))
        json.dump(out, open(a[2], "w"), indent=1)
    elif a[0] == "presets":
        # presets <fits.json> <her_fits.json> <out.json> [--k K] name=ref ...: each preset its reference's fit less
        # what her own references' fits share (how a painting's landmarks differ from a render's, the same for
        # every face, not how this face differs from hers), that difference drawn out K times (a face's own
        # character, as the research has it: away from the average in its own direction), within -1 to 1.
        fits = json.load(open(a[1], encoding="utf-8-sig"))
        hers = json.load(open(a[2], encoding="utf-8-sig"))
        k = float(a[a.index("--k") + 1]) if "--k" in a else 1.6
        bias = {s: float(np.mean([f.get(s, 0.0) for f in hers.values()])) for s in keyed()}
        out = {}
        for arg in a[4:]:
            if "=" not in arg:
                continue
            name, ref = arg.split("=", 1)
            v = {s: round(float(np.clip(k * (fits[ref].get(s, 0.0) - bias[s]), -1, 1)), 2) for s in keyed()}
            out[name] = {s: x for s, x in v.items() if abs(x) >= 0.04}
            print("PRESET", name, "from", ref, json.dumps(out[name]))
        json.dump(out, open(a[3], "w"), indent=1)
    elif a[0] == "lab":
        fits = json.load(open(a[1], encoding="utf-8-sig"))
        json.dump({n: to_targets(v) for n, v in fits.items()}, open(a[2], "w"), indent=1)
        print(len(fits), "faces for the lab")
