"""Join built P4 clips end to end into one review clip (godot/art/people/body_p1/p4/<out>.json), for shots of a chain.
Usage: python tools/anim/p4_concat.py <out_name> <clip> <clip> ...
A join drops the next clip's frame 0 when it equals the previous clip's last frame within 0.1 deg (every bone's rotation);
the root/pelvis position step at each join is printed too (kept as built: the game plays each clip from its own start).
Loop false; contacts, beats (contact lists, offset per segment; cancel = the last segment's; blend_in = the first's) carried.
Review only: pack it with tools/anim/p4_pack.sh --review=<out_name>,..."""
import json, math, sys
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "godot" / "art" / "people" / "body_p1" / "p4"


def deg(a, b):
    d = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2 * math.acos(min(1.0, d)))


def qrot(q, v):
    x, y, z, w = q
    u = (x, y, z); c = lambda a, b: (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    t = c(u, v); t = tuple(2 * k for k in t); t2 = c(u, t)
    return tuple(v[i] + w * t[i] + t2[i] for i in range(3))


def pelvis_world(c, f):
    """Pelvis world position at frame f: root position + root rotation applied to the pelvis' local position."""
    r = qrot(c["rot"]["root"][f], tuple(c["pos"]["pelvis"][f]))
    return tuple(a + b for a, b in zip(c["pos"]["root"][f], r))


def main(out, names):
    cl = [json.load(open(D / f"{n}.json")) for n in names]
    r = cl[0]
    res = {k: v for k, v in r.items() if k not in ("rot", "pos", "contacts", "beats", "frames", "loop", "name", "source", "fit")}
    res.update(name=out, loop=False, source={"concat": names}, fit=[])
    bones = r["bones"]
    rot = {b: list(r["rot"][b]) for b in r["rot"]}
    pos = {b: list(r["pos"][b]) for b in r["pos"]}
    contacts = {k: [list(x) for x in v] for k, v in r["contacts"].items()}
    beats = {"contact": list(r.get("beats", {}).get("contact", []))}
    if "blend_in" in r.get("beats", {}): beats["blend_in"] = r["beats"]["blend_in"]
    if "cancel" in r.get("beats", {}): beats["cancel"] = r["beats"]["cancel"]
    total = r["frames"]
    for prev, c in zip(cl, cl[1:]):
        assert c["fps"] == r["fps"] and c["bones"] == bones, "fps/bones differ"
        worst = max(deg(rot[b][-1], c["rot"][b][0]) for b in rot)
        pstep = {b: math.dist(pos[b][-1], c["pos"][b][0]) * 100 for b in pos}
        pw = math.dist(pelvis_world(prev, -1), pelvis_world(c, 0)) * 100
        drop = 1 if worst <= 0.1 else 0
        print(f"join {prev['name']} -> {c['name']}: last/first max {worst:.3f} deg, pos step cm "
              + ", ".join(f"{b} {v:.2f}" for b, v in pstep.items()) + f", pelvis WORLD {pw:.2f}" + (" : duplicate frame dropped" if drop else " : NOT equal, no frame dropped"))
        for b in rot: rot[b] += c["rot"][b][drop:]
        for b in pos: pos[b] += c["pos"][b][drop:]
        off = total - drop
        for k, v in c["contacts"].items():
            contacts.setdefault(k, []).extend([a + off, z + off] for a, z in v)
        cb = c.get("beats", {})
        beats["contact"] += [round(t + off / r["fps"], 4) for t in cb.get("contact", [])]
        if "cancel" in cb: beats["cancel"] = round(cb["cancel"] + off / r["fps"], 4)
        total += c["frames"] - drop
    res.update(frames=total, rot=rot, pos=pos, contacts=contacts, beats=beats)
    json.dump(res, open(D / f"{out}.json", "w"))
    print(f"wrote {out}.json: {total} frames, {total / r['fps']:.3f} s")


if __name__ == "__main__":
    if len(sys.argv) < 4: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
