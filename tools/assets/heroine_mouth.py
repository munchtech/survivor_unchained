"""Her mouth's inside seated for an open mouth and a smile, in her exported glb (heroine.glb).

The smile pass (the owner, 13 October 2026: "queue the smile pass after the face ships"). With her mouth open
(mouth_open .6, with or without smile .8) no upper teeth showed: a front ray down her mouth's middle met her upper
lip, then 7-10 mm of TONGUE (the "salmon slab" under her upper lip), then her lower teeth. The causes, all in the
MakeHuman parts as fitted to her sculpt:
- her teeth sat high: the upper incisors' edges 1-3 mm ABOVE the front edge of her upper lip (which mouth_open leaves
  where it is), so it hid them in every pose; a relaxed open mouth shows 2-4 mm of them, a smile most of the crown.
  Her faces' keys move her lips by different amounts, so the seat is each face's own (SEAT_MM);
- mouth_open moved her upper teeth too (by her upper lip's drag, 1.3 mm down): they are her skull's;
- her tongue barely followed her jaw (3 mm while her lower teeth dropped 10), so it stood up behind her upper lip;
- her smile raised her mouth's corners and not her upper lip's middle (0.1 mm), so a smile with her mouth open showed
  no more teeth than her mouth open alone.
So: her teeth and tongue seated lower (her own face's SEAT_MM in their rest shape, each other face's difference in its
face key: her closed lips cover them as before); mouth_open moves only her lower teeth and, by the lower teeth nearest
each of its points, her tongue; and a new key on her head, smile_open (her upper lip's middle raised RAISE_MM,
rolled back a little), which People.HerFace sets as smile times how far her mouth is open (her lips closed, a smile
stays closed-lipped).

    python tools/assets/heroine_mouth.py [GLB [OUT]]

On one already done (her teeth mesh's extras say mouth_seat) it does nothing. heroine_outfits.py runs it on the body
it exports, after the teeth's shade. Numpy only (it runs in Blender's Python).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "godot", "art", "people", "heroine.glb")
# (mm lower, per face: each face's upper incisors 2.5 mm under her upper lip's front edge at mouth_open .6, measured by
# front rays down her mouth's middle with the teeth 4.5 mm lower: own 3.0, doe 0.8, fey 2.0, hardwon 0.4, highborn 1.2,
# moonlit 2.2, saffron 0.4, sunborn 1.2, vixen 1.6, wildling 1.8 mm shown)
SHOWN_AT_45 = {"own": 3.0, "doe": 0.8, "fey": 2.0, "hardwon": 0.4, "highborn": 1.2, "moonlit": 2.2, "saffron": 0.4,
               "sunborn": 1.2, "vixen": 1.6, "wildling": 1.8}
SHOW_MM = float(os.environ.get("MOUTH_SHOW_MM", "2.5"))
SEAT_MM = {f: 4.5 + SHOW_MM - s for f, s in SHOWN_AT_45.items()}
K = 16                         # (lower-teeth points each tongue point follows)
JAW_SHARE = 0.5                # (her lower teeth: the points mouth_open moves more than this share of its most)
RAISE_MM = float(os.environ.get("MOUTH_RAISE_MM", "3.5"))   # (smile_open at 1: her upper lip's middle raised so far)
ROLL = 0.25                    # (and rolled back by this share of it)
UP_X, UP_X2 = 0.012, 0.020     # (m from her mouth's middle: raised fully to here, easing out to there, where her smile
#                                already lifts her mouth's corners 5-9 mm)
UP_Y1, UP_Y2 = 0.008, 0.016    # (m above her lips' line: raised fully to here, easing out to there, under her nose)
LINE_NEAR = 1.692              # (her lips' line is looked for within 2 cm of this height, m)
CAV_AXIS_Z, CAV_FRONT, CAV_SIDE, CAV_DEPTH = 0.04, 0.088, 0.6, 0.025   # (m: her mouth's axis; its opening's z at her
#                                middle, falling back CAV_SIDE per metre out; dark at CAV_DEPTH behind it)
TONGUE_ROOT, TONGUE_LEN = 0.3, 0.05   # (her tongue's shade at its root, so far back from its tip)


def _prim(js, mat):
    mats = [m.get("name") for m in js.get("materials", [])]
    hit = [(m, p) for m in js["meshes"] for p in m["primitives"] if "material" in p and mats[p["material"]] == mat]
    if len(hit) != 1:
        raise SystemExit("MOUTH: found %d %s primitives" % (len(hit), mat))
    return hit[0]


def _s01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def lips_line(V, D):
    """Her lips' line (y, m) at her mouth's middle: where mouth_open's move jumps (her lower lip goes with her jaw)."""
    n = np.linalg.norm(D, axis=1)
    ys = []
    for x0 in np.arange(0, 0.0141, 0.002):
        s = (np.abs(np.abs(V[:, 0]) - x0) < 0.001) & (np.abs(V[:, 1] - LINE_NEAR) < 0.02) & (V[:, 2] > 0.05)
        i = np.where(s)[0][np.argsort(-V[s, 1])]
        k = np.argmax(np.abs(np.diff(n[i])))
        ys.append(0.5 * (V[i[k], 1] + V[i[k + 1], 1]))
    return float(np.median(ys))


def smile_open(V, D):
    """smile_open's move: her upper lip (above her lips' line, and moved little by mouth_open, as her lower lip's points
    go 20-40 mm with her jaw) raised RAISE_MM in her mouth's middle and rolled back ROLL of that."""
    line = lips_line(V, D)
    n = np.linalg.norm(D, axis=1)
    w = (_s01((V[:, 1] - line + 0.004) / 0.001) * (1 - _s01((V[:, 1] - line - UP_Y1) / (UP_Y2 - UP_Y1)))
         * (1 - _s01((np.abs(V[:, 0]) - UP_X) / (UP_X2 - UP_X))) * (1 - _s01((n - 0.008) / 0.006)))
    out = np.zeros_like(V)
    out[:, 1] = RAISE_MM / 1000 * w
    out[:, 2] = -ROLL * RAISE_MM / 1000 * w
    return out, line, int((w > 0.5).sum())


def _add_target(js, chunks, mesh, prim, name, vals):
    js["accessors"].append({"componentType": 5126, "count": len(vals), "type": "VEC3"})
    i = len(js["accessors"]) - 1
    hs._set(js, chunks, i, vals, minmax=True)
    prim.setdefault("targets", []).append({"POSITION": i})
    mesh.setdefault("extras", {}).setdefault("targetNames", []).append(name)
    if "weights" in mesh:
        mesh["weights"].append(0.0)


def _add_colour(js, chunks, prim, rgba):
    js["accessors"].append({"componentType": 5126, "count": len(rgba), "type": "VEC4"})
    i = len(js["accessors"]) - 1
    a = js["accessors"][i]
    a["bufferView"] = len(js["bufferViews"])
    js["bufferViews"].append({"buffer": 0})
    chunks[a["bufferView"]] = np.ascontiguousarray(rgba.astype("<f4")).tobytes()
    prim["attributes"]["COLOR_0"] = i


def seat(path, out=None):
    js, binc = hs._load(path)
    tm, tp = _prim(js, "teeth")
    gm, gp = _prim(js, "tongue")
    hm, hp = _prim(js, "skin_head")
    if "mouth_seat" in tm.get("extras", {}):
        print("MOUTH: already done in", path, "- nothing done")
        return
    if len(hm["primitives"]) != 1:
        raise SystemExit("MOUTH: her head's mesh has %d primitives (one expected)" % len(hm["primitives"]))
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    rd = lambda i: hs._read(js, binc, i).astype(np.float64)  # noqa: E731
    TV, GV, HV = rd(tp["attributes"]["POSITION"]), rd(gp["attributes"]["POSITION"]), rd(hp["attributes"]["POSITION"])
    tn, gn, hn = tm["extras"]["targetNames"], gm["extras"]["targetNames"], hm["extras"]["targetNames"]
    TD = rd(tp["targets"][tn.index("mouth_open")]["POSITION"])
    HD = rd(hp["targets"][hn.index("mouth_open")]["POSITION"])
    n = np.linalg.norm(TD, axis=1)
    jaw = n > JAW_SHARE * n.max()
    # (the tongue moved as the lower teeth nearest it: inverse-distance over its K nearest. A rigid fit of the lower
    # teeth's move was poor, rms 2.2 mm, as MakeHuman's jaw is a morph, and it swung the tongue's root 31 mm)
    dd = np.linalg.norm(GV[:, None] - TV[jaw][None], axis=2)
    j = np.argsort(dd, 1)[:, :K]
    w = 1 / np.maximum(np.take_along_axis(dd, j, 1), 1e-4) ** 2
    w /= w.sum(1, keepdims=True)
    GD_old = rd(gp["targets"][gn.index("mouth_open")]["POSITION"])
    GD = (w[..., None] * TD[jaw][j]).sum(1)
    # (her upper teeth are her skull's: mouth_open no longer moves them)
    TD2 = TD * _s01((n / n.max() - 0.3) / (JAW_SHARE - 0.3))[:, None]
    SO, line, raised = smile_open(HV, HD)
    # (each accessor written anew: a shared view would move other parts too)
    hs._set(js, chunks, gp["targets"][gn.index("mouth_open")]["POSITION"], GD, minmax=True)
    hs._set(js, chunks, tp["targets"][tn.index("mouth_open")]["POSITION"], TD2, minmax=True)
    dy = np.array([0, -SEAT_MM["own"] / 1000, 0])
    hs._set(js, chunks, tp["attributes"]["POSITION"], TV + dy, minmax=True)
    hs._set(js, chunks, gp["attributes"]["POSITION"], GV + dy, minmax=True)
    for f, mm in SEAT_MM.items():
        if f == "own":
            continue
        extra = np.array([0, -(mm - SEAT_MM["own"]) / 1000, 0])
        for m, p, names in ((tm, tp, tn), (gm, gp, gn)):
            if "face_" + f in names:
                a = p["targets"][names.index("face_" + f)]["POSITION"]
                hs._set(js, chunks, a, rd(a) + extra, minmax=True)
    _add_target(js, chunks, hm, hp, "smile_open", SO)
    # (the inside of her mouth, for heroine_skin.gdshader's mouth_in: her head's vertex colour's alpha, 1 outside,
    # falling to 0 with depth behind her lips, on the points facing in toward her mouth's middle; and her tongue's
    # vertex colour, its own shade, lit at its tip and dark at its root)
    HN = rd(hp["attributes"]["NORMAL"])
    c0 = np.array([0.0, line, CAV_AXIS_Z])
    inside = (((c0 - HV) * HN).sum(1) > 0) & (np.abs(HV[:, 0]) < 0.035) & (np.abs(HV[:, 1] - line) < 0.025)
    front = CAV_FRONT - CAV_SIDE * np.abs(HV[:, 0])
    depth = np.where(inside, _s01((front - HV[:, 2]) / CAV_DEPTH), 0.0)
    _add_colour(js, chunks, hp, np.c_[np.ones((len(HV), 3)), 1 - depth])
    gs = 1 - (1 - TONGUE_ROOT) * _s01((GV[:, 2].max() - GV[:, 2]) / TONGUE_LEN)
    _add_colour(js, chunks, gp, np.c_[np.repeat(gs[:, None], 3, 1), np.ones(len(GV))])
    tm.setdefault("extras", {})["mouth_seat"] = {"seat_mm": SEAT_MM, "tongue_k": K, "raise_mm": RAISE_MM,
                                                 "line": round(line, 5)}
    hs._save(out or path, js, chunks)
    print("MOUTH: teeth and tongue seated %s mm lower (own %.1f); mouth_open no longer moves her upper teeth; the tongue "
          "follows %d lower-teeth points (its mouth_open was %.1f mm at most, now %.1f); smile_open raises %d points of "
          "her upper lip %.1f mm (lips' line y %.4f); written %s" % (
              ", ".join("%s %.1f" % kv for kv in SEAT_MM.items() if kv[0] != "own"), SEAT_MM["own"], jaw.sum(),
              1000 * np.linalg.norm(GD_old, axis=1).max(), 1000 * np.linalg.norm(GD, axis=1).max(), raised, RAISE_MM,
              line, out or path))


if __name__ == "__main__":
    a = sys.argv[1:]
    seat(a[0] if a else GLB, a[1] if len(a) > 1 else None)
