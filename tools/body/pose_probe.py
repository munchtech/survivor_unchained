#!/usr/bin/env python3
"""The pose ruler's table: A against B from two --pose-probe files (P1PoseProbe.cs: a JSON line per sampled frame).
usage: pose_probe.py A.jsonl B.jsonl [--frame N] [--match]
--frame N: A's frame nearest N (default its last). --match: B's frame nearest A's by arm and leg directions (a moving clip's phase);
otherwise B's frame with the same number. Directions: each role's joint to its next joint, world; deg = angle A to B.
Heights: over the actor's ground, mm. Drops: below Head, mm."""
import json, math, sys

CH = [("pelvis>spine_top", "pelvis", "spine_03"), ("spine_top>neck", "spine_03", "neck_01"), ("neck>Head", "neck_01", "Head")]
for s in "lr":
    CH += [(f"clavicle>shoulder_{s}", f"clavicle_{s}", f"upperarm_{s}"), (f"upperarm_{s}", f"upperarm_{s}", f"lowerarm_{s}"),
           (f"forearm_{s}", f"lowerarm_{s}", f"hand_{s}"), (f"hand_{s}", f"hand_{s}", f"middle_01_{s}"),
           (f"thigh_{s}", f"thigh_{s}", f"calf_{s}"), (f"calf_{s}", f"calf_{s}", f"foot_{s}"), (f"foot_{s}", f"foot_{s}", f"ball_{s}")]
HEIGHTS = ["pelvis", "spine_03", "neck_01", "Head", "crown", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r",
           "hand_l", "hand_r", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"]


REST = {}


def load(p):
    rows = [json.loads(l) for l in open(p) if l.strip()]
    REST[len(REST)] = next((r for r in rows if "rest" in r), None)
    return [r for r in rows if "frame" in r]


def rel(f, r):
    """A bone's rest-relative world turn as (fwd, up)."""
    return f["bones"][r]["fwd"], f["bones"][r]["up"]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def ang(a, b):
    la, lb = math.hypot(*a), math.hypot(*b)
    return math.degrees(math.acos(max(-1, min(1, sum(x * y for x, y in zip(a, b)) / (la * lb)))))


def d(f, a, b):
    return sub(f["bones"][b]["p"], f["bones"][a]["p"])


def pitch(v):
    return math.degrees(-math.asin(max(-1, min(1, v[1] / math.hypot(*v)))))


def table(A, B, out=print):
    ga, gb = A["ground"], B["ground"]
    out(f"frames A {A['frame']} B {B['frame']}; ground A {ga:.4f} B {gb:.4f}")
    out("height over ground, mm       A         B      B-A")
    for r in HEIGHTS:
        a, b = (A["bones"][r]["p"][1] - ga) * 1000, (B["bones"][r]["p"][1] - gb) * 1000
        out(f"{r:22} {a:8.1f} {b:9.1f} {b - a:8.1f}")
    out("direction (joint to next)   deg A-B")
    worst = 0
    for n, p, q in CH:
        v = ang(d(A, p, q), d(B, p, q))
        out(f"{n:26} {v:6.2f}")
        worst = max(worst, v)
    out(f"worst joint-line direction {worst:.2f} deg (rests differ: see the rest-relative turns)")
    out("rest-relative turn, deg A-B (fwd axis, up axis)")
    wt = 0
    for r in A["bones"]:
        if r == "crown" or r.startswith(("middle", "spine_01")):
            continue
        fa, ua = rel(A, r)
        fb, ub = rel(B, r)
        x, y = ang(fa, fb), ang(ua, ub)
        wt = max(wt, x, y)
        out(f"{r:22} {x:6.2f} {y:6.2f}")
    out(f"worst rest-relative {wt:.2f} deg")
    for r, lab in (("spine_03", "chest"), ("Head", "head")):
        fa, fb = A["bones"][r]["fwd"], B["bones"][r]["fwd"]
        out(f"{lab} forward: pitch below level A {pitch(fa):.2f} B {pitch(fb):.2f} (diff {pitch(fb) - pitch(fa):+.2f}); angle {ang(fa, fb):.2f} deg")
    lr = []
    for lab, F in (("A", A), ("B", B)):
        h = F["bones"]["Head"]["p"][1]
        ul, ur = F["bones"]["upperarm_l"]["p"][1], F["bones"]["upperarm_r"]["p"][1]
        cl, cr = F["bones"]["clavicle_l"]["p"][1], F["bones"]["clavicle_r"]["p"][1]
        lr.append((ul - ur) * 1000)
        out(f"{lab}: shoulder joint below Head L {(h - ul) * 1000:.1f} R {(h - ur) * 1000:.1f} mm; clavicle head below Head L {(h - cl) * 1000:.1f} R {(h - cr) * 1000:.1f} mm; shoulder L-R {lr[-1]:+.1f} mm")
    out(f"shoulder L-R, B-A {lr[1] - lr[0]:+.1f} mm")
    return worst


if __name__ == "__main__":
    args = sys.argv[1:]
    match = "--match" in args
    fr = int(args[args.index("--frame") + 1]) if "--frame" in args else None
    files = [x for x in args if x.endswith(".jsonl")]
    a, b = load(files[0]), load(files[1])
    A = min(a, key=lambda f: abs(f["frame"] - fr)) if fr is not None else a[-1]
    if match:
        LEG = [x for x in CH if x[0].startswith(("thigh", "calf", "upperarm", "forearm"))]
        B = min(b, key=lambda f: sum(ang(d(A, p, q), d(f, p, q)) for _, p, q in LEG))
    else:
        B = min(b, key=lambda f: abs(f["frame"] - A["frame"]))
    if REST.get(0) and REST.get(1):
        ra, rb = REST[0], REST[1]
        print("rest heights, skeleton space, mm    A         B      B-A")
        for r in ra["rest"]:
            if r in rb["rest"]:
                print(f"{r:30} {ra['rest'][r][1] * 1000:8.1f} {rb['rest'][r][1] * 1000:9.1f} {(rb['rest'][r][1] - ra['rest'][r][1]) * 1000:8.1f}")
        print(f"{'crown':30} {ra['crown_rest'][1] * 1000:8.1f} {rb['crown_rest'][1] * 1000:9.1f} {(rb['crown_rest'][1] - ra['crown_rest'][1]) * 1000:8.1f}")
        print("meshes A:", ra["meshes"])
        print("meshes B:", rb["meshes"])
    table(A, B)
