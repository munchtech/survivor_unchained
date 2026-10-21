#!/usr/bin/env python3
"""Which house each village piece of a zone's props.json belongs to (E9b1), and each house's look.

    python tools/godot/house_ids.py [zone]      (default: waystation)

export_zone.mjs writes a house's (or a town wall's) pieces one after another, its roof last
(houses.ts buildHouse: the storeys' walls, corners, then the roof, its gable fronts, the chimney).
So a run of village wall pieces up to a roof is one house; a run's pieces far from the house at its
end (a town wall written before a gate tower) are walls of their own, split where the run jumps
more than 9 m. Each row gets "h": its house's number (props.json, in place; rows of no house keep none).

Then each house's look, so neighbors differ (look bible 08: "neighboring buildings differ in at
least two of roof, color and height"): a plaster tint (0-5) and a timber treatment (0 plain plaster,
1 framed with crosses, 2 framed with braces), chosen greedily so no two houses within 18 m share a
tint, and they share a treatment only when no other is left; written to props_own.json "walls"
"houses": {"<h>": [tint, treatment, roof covering, roof tint]} (the rest of props_own.json kept). The roof's
rows (its body, gable fronts, chimney) take their house's number too (E9b2).
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    zone = sys.argv[1] if len(sys.argv) > 1 else "waystation"
    d = ROOT / "godot" / "data" / "zones" / zone
    rows = json.loads((d / "props.json").read_text())
    for r in rows:
        r.pop("h", None)
    runs, cur = [], []
    for i, r in enumerate(rows):
        s = r["id"].split("/")[-1]
        if r["id"].startswith("village/") and not s.startswith(("Roof", "Prop_")):
            cur.append(i)
        elif cur:
            runs.append((cur, s.startswith("Roof")))
            cur = []
    if cur:
        runs.append((cur, False))

    def org(i):
        t = rows[i]["t"]
        return t[9], t[10], t[11]

    hid = 0
    houses = {}  # h -> (cx, cz, is_house)
    for run, roofed in runs:
        segs = [[run[0]]]
        for a, b in zip(run, run[1:]):
            (ax, ay, az), (bx, by, bz) = org(a), org(b)
            if math.hypot(ax - bx, az - bz) > 9 or abs(ay - by) > 3.6:
                segs.append([b])
            else:
                segs[-1].append(b)

        def bbox(seg):
            xs = [org(i)[0] for i in seg]
            zs = [org(i)[2] for i in seg]
            return min(xs) - 1, max(xs) + 1, min(zs) - 1, max(zs) + 1
        last = bbox(segs[-1])
        groups = {}
        for seg in segs:
            b = bbox(seg)
            overl = roofed and not (b[1] < last[0] or b[0] > last[1] or b[3] < last[2] or b[2] > last[3])
            key = "house" if overl else id(seg)
            groups.setdefault(key, []).extend(seg)
        for key, seg in groups.items():
            for i in seg:
                rows[i]["h"] = hid
            xs = [org(i)[0] for i in seg]
            zs = [org(i)[2] for i in seg]
            houses[hid] = ((min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2, key == "house")
            hid += 1

    # each house's look: greedy, the most crowded first
    ids = [h for h, v in houses.items() if v[2]]
    near = {h: [o for o in ids if o != h and math.hypot(houses[h][0] - houses[o][0], houses[h][1] - houses[o][1]) < 18] for h in ids}
    look = {}
    used_t, used_s = [0] * 6, [0] * 3
    for h in sorted(ids, key=lambda h: -len(near[h])):
        nt = {look[o][0] for o in near[h] if o in look}
        ns = [look[o][1] for o in near[h] if o in look]
        t = min((t for t in range(6) if t not in nt), key=lambda t: (used_t[t], t), default=h % 6)
        s = min(range(3), key=lambda s: (ns.count(s), used_s[s], s))
        look[h] = [t, s]
        used_t[t] += 1
        used_s[s] += 1
    # each house's roof (E9b2): its covering (0 clay pantiles, 1 oak shingles) and that covering's tint (0-3), so
    # neighbors differ: no two houses within 18 m share both, the nearest three mostly differ in covering
    used_r = {}
    for h in sorted(ids, key=lambda h: -len(near[h])):
        by_d = sorted(near[h], key=lambda o: math.hypot(houses[h][0] - houses[o][0], houses[h][1] - houses[o][1]))
        def cost(rt, ti):
            same = sum(1 for o in near[h] if len(look[o]) > 2 and look[o][2:] == [rt, ti])
            close = sum(1 for o in by_d[:3] if len(look[o]) > 2 and look[o][2] == rt)
            return 4 * same + 1.5 * close + 0.3 * used_r.get((rt, ti), 0) + (0.4 if rt == 1 else 0.0)
        rt, ti = min(((rt, ti) for rt in range(2) for ti in range(4)), key=lambda c: (cost(*c), c))
        look[h] += [rt, ti]
        used_r[(rt, ti)] = used_r.get((rt, ti), 0) + 1
    # the roof's rows (its body, gable fronts and chimney, written after its walls) take the house's number
    cur = -1
    for r in rows:
        s_ = r["id"].split("/")[-1]
        if not r["id"].startswith("village/"):
            continue
        if s_.startswith(("Roof", "Prop_Chimney")):
            if cur >= 0:
                r["h"] = cur
        elif "h" in r:
            cur = r["h"] if houses.get(r["h"], (0, 0, False))[2] else -1

    (d / "props.json").write_text(json.dumps(rows, separators=(",", ":")) + chr(10))
    own_path = d / "props_own.json"
    own = json.loads(own_path.read_text()) if own_path.exists() else {}
    own.setdefault("walls", {})["houses"] = {str(h): v for h, v in sorted(look.items())}
    own_path.write_text(json.dumps(own, indent=1))
    print(f"{zone}: {hid} groups, {len(ids)} houses; tints {used_t}, treatments {used_s}, roofs {sorted(used_r.items())}")


if __name__ == "__main__":
    main()
