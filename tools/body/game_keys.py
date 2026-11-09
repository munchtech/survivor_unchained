#!/usr/bin/env python3
"""Game key poses for the correctives (P1 R1 weights round 19): A's and B's skeletons as the game posed them in one shot.

    python tools/body/game_keys.py tools/body/ref/game_keys.json look=A_probe.jsonl,B_probe.jsonl [close=...] [--note "..."]

Each probe is a --pose-probe-full dump (P1PoseProbe.cs: every bone's skeleton-space pose at the shot's last frame, the
nonzero blend-shape weights). Writes, per key: "a" (A's bones, 12 numbers each: basis columns then origin), "a_shapes" (A's
active body shapes), "b" (B's bones), "b_shapes" (B's active body shapes), "frame", the source paths. correctives.py's
"game_a" fold poses B with "b" and lays it on A's surface posed with "a" (rest twins). B's key pose is B's own game pose,
so a rest skeleton change or a clip re-bake that moves B's arm calls for a fresh probe and this file re-made.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from posed_fit import read_probe  # noqa: E402

BODY = "Heroine"


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    note = sys.argv[sys.argv.index("--note") + 1] if "--note" in sys.argv else ""
    args = [x for x in args if x != note]
    out, pairs = args[0], args[1:]
    keys = {}
    for kv in pairs:
        k, v = kv.split("=", 1)
        pa_, pb_ = v.split(",")
        pa, pb = read_probe(pa_), read_probe(pb_)
        r = lambda q: [round(float(x), 7) for x in q]
        keys[k] = {"frame": [pa.get("frame"), pb.get("frame")], "source": [pa_.replace("\\", "/"), pb_.replace("\\", "/")],
                   "a": {n: r(m) for n, m in pa["bones"].items()},
                   "a_shapes": {n: float(w) for n, w in pa["meshes"].get(BODY, {}).get("shapes", {}).items()},
                   "b": {n: r(m) for n, m in pb["bones"].items()},
                   "b_shapes": {n: float(w) for n, w in pb["meshes"].get(BODY, {}).get("shapes", {}).items()}}
    doc = {"about": "Game key poses (tools/body/game_keys.py; read by correctives.py's \"game_a\" fold): A's and B's bones "
                    "(skeleton space) in the same game shot, from --pose-probe-full dumps. " + note,
           "made": time.strftime("%Y-%m-%d %H:%M"), "keys": keys}
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        json.dump(doc, f, separators=(",", ":"))
    print("wrote", out, {k: len(v["b"]) for k, v in keys.items()})


if __name__ == "__main__":
    main()
