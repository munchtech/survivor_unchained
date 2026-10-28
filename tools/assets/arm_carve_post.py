"""Her arms' rest CARVE, round 3 (Body 19, 27 Oct 2026), after arm_sculpt_post. Two rounds of ADDED ~5 mm masses failed
blind max judges: at the town close-up 1 mm ~ 0.9 px, and a feminine athletic arm reads through its OUTLINE alternating
wide / narrow (cap, a narrower insertion, the biceps, a NARROW point above the elbow, the elbow's bony POINT, the forearm's
swell, a narrow FLAT wrist). Hers was an even tube. So this step takes the narrow points IN, by amounts that move her
outline >= 6 px at the game's cameras (judge 2's fixes 2, 3, 5; the owner: "not toned or sexy", "clunky"):

  UP (radial, on heroine_arm_tone's upper-arm chart: t = s / humerus from her shoulder joint's level, phi 0 front,
      90 out, 180 back, -90 in; mm, + out):
      the outer-back arm just below the deltoid's insertion (so the cap overhangs as a step in the front 3/4 outlines;
      nothing at the shoulder's tip: the Look's shoulder line is unchanged), the lower third's front and back (the waist
      above the elbow; the triceps' tendon flat), the elbow's back (bony: a narrow back, not a sausage end) with the
      olecranon left as a narrow point, and the brachioradialis' origin rising on the outer side above the joint;
  FORE (along her normal, on arm_sculpt_post's forearm chart round its centre line: t2 from the elbow in forearm
      lengths, phi 0 radial (thumb), 90 dorsal, 180 ulnar, -90 palmar in her bind pose):
      the brachioradialis / extensor swell high on the outer forearm, and the wrist narrower and FLAT (palmar and
      dorsal faces in: a wrist about two thirds as deep as it is wide, not round).

Each taken by her arm's share of the skinning and smoothed over her surface (arm_sculpt_post.moves, its deltoid and
wedge off); positions and normals; her shoulder PSDs kept valid as arm_sculpt_post keeps them (arm_contour_post.psd_keep).
Her skin's relief (arm_sculpt_post's bake) is left as it is: it rides the surface.

    python tools/assets/arm_carve_post.py <in heroine.glb> <out heroine.glb>
Idempotent: done-mark arm_carve (a marked body is copied unchanged). Bare body only: outfits follow later.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arm_contour_post as ac  # noqa: E402
import arm_sculpt_post as asp  # noqa: E402

MARK = "arm_carve"
_E = os.environ.get
AMT = float(_E("CARVE_AMT", "1.0"))
# (t0, phi0, half-length t, half-width deg, mm): final mm before smoothing (no arm_sculpt_post AMT)
UP = (
    (0.54, 115, 0.12, 75, -10.0),   # outer-back arm just below the insertion: the cap's step
    (0.80, 0, 0.16, 65, -10.0),     # the lower third's front: the waist above the elbow
    (0.84, 180, 0.15, 65, -9.5),    # its back: the triceps' tendon, flat
    (1.00, 180, 0.09, 90, -12.0),   # the elbow's back: bony, narrow
    (0.99, 180, 0.05, 25, 7.0),     # the olecranon, a point left proud of it
    (0.92, 80, 0.10, 45, 5.5),      # the brachioradialis' origin, rising on the outer side above the joint
)
FORE = (
    (0.15, 70, 0.17, 75, 8.0),      # brachioradialis / extensors (the mobile wad): the outer forearm's swell, 30-50 mm below the joint
    (0.86, 90, 0.18, 85, -8.0),     # the wrist's dorsal face in
    (0.86, -90, 0.18, 85, -8.0),    # and its palmar face: flat
    (0.80, 0, 0.25, 180, -1.5),     # the lower forearm slimmer all round
)
SMOOTH = int(_E("CARVE_SMOOTH", "2"))


def moves(b, up=UP, fore=FORE, amt=AMT, smooth=SMOOTH):
    return asp.moves(b, up=up, fore=fore, wedge={}, amt=amt, smooth=smooth, delt=False)


def run(src, dst, up=UP, fore=FORE, quiet=False):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    g = G.g
    ex = g.setdefault("asset", {}).setdefault("extras", {})
    if ex.get(MARK):
        print("ARM_CARVE: %s has had it" % dst)
        return None
    if not ex.get(asp.MARK):
        print("ARM_CARVE: note, %s has no %s (the carve is tuned on it)" % (dst, asp.MARK))
    b = ph.Body(G)
    dU, info = moves(b, up=up, fore=fore)
    n0 = ph.vn(b.U, b.F)
    n1 = ph.vn(b.U + dU, b.F)
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in prims:
        ai, ni = p["attributes"]["POSITION"], p["attributes"]["NORMAL"]
        X = G.get(ai).astype(float)
        w = b.wid[o:o + len(X)]
        o += len(X)
        X = X + dU[w]
        N = G.get(ni).astype(float) + (n1 - n0)[w]
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32))
        G.put(ni, N.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
    rep = {}
    ac.psd_keep(G, prims, b.wid, dU, n1 - n0, rep)
    mv = np.linalg.norm(dU, axis=1) * 1000
    ex[MARK] = {"up": [list(x) for x in up], "fore": [list(x) for x in fore], "amt": AMT, "smooth": SMOOTH,
                "max_mm": round(float(mv.max()), 2)}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    if not quiet:
        print("ARM_CARVE: %d points moved > 0.5 mm, max %.1f mm -> %s" % ((mv > 0.5).sum(), mv.max(), dst))
        for k, v in info.items():
            print("  %s %s" % (k, json.dumps(v)))
        print("  psd kept (points, max mm taken back): " + ", ".join("%s %d/%.1f" % (k, v[0], v[1]) for k, v in rep.items()))
    return info


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    run(a[0], a[1])
