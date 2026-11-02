#!/usr/bin/env python3
"""Lamps board v2 LAYOUT (docs/design/CLASS_IDENTITY_AND_TALENTS.md section 3.2).

Reads godot/data/content/lamps.json (v1, read-only), drops the 72 skill lamps, adds the v2 lamps
and writes godot/data/content/board_v2.json (ids, kinds, regions, groups, positions, edges; no
texts or effects) plus a preview at godot/.shots/board_v2.png.  Stdlib + matplotlib only.

Frame: board units, y up, the Ford hub at (0,0).  Every callings' quarter is the reaver quarter
turned by 90 degrees (the whole board is four-fold symmetric apart from the kind of the diagonal
hung lamps); within a quarter the two roads are mirror images.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
V1 = os.path.join(ROOT, "godot", "data", "content", "lamps.json")
OUT = os.path.join(ROOT, "godot", "data", "content", "board_v2.json")
PNG = os.path.join(ROOT, "godot", ".shots", "board_v2.png")

CALLINGS = ["reaver", "arcanist", "stalker", "warden"]
QUARTER = {"reaver": 45, "arcanist": 135, "stalker": 225, "warden": 315}
ROAD_ANGLE = {"butcher": 23, "chainbound": 67, "moonweaver": 113, "kindler": 157,
              "verge_hunter": 203, "roadknife": 247, "bulwark": 293, "sunderer": 337}
PATHS = [("steel", 0, "Steel and Blood"), ("host", 36, "The Host"), ("storm", 72, "The Storm"),
         ("grave", 108, "The Grave"), ("weave", 135, "The Weave"), ("pyre", 165, "The Pyre"),
         ("rime", 195, "The Long Winter"), ("wild", 230, "The Wild"), ("hunt", 280, "The Hunt"),
         ("dawn", 320, "Dawn's Light")]
RING_NAMES = {"shambles": "Shambles", "night_road": "The Night Road", "firebreak": "Firebreak",
              "duelists_road": "Duelist's Road"}
DIAG = {"vigil": ("The Vigil", "arcanist", "warden", 135), "poachers": ("Poacher's Crossing", "reaver", "stalker", 45)}


def dv(a):
    return math.cos(math.radians(a)), math.sin(math.radians(a))


def pol(r, a):
    c, s = dv(a)
    return r * c, r * s


def norm(a):
    return a % 360


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


# ------------------------------------------------------------------ model --
lamps, by_id, groups = [], {}, []


def add(lid, kind, region, group, pos, at=(), calling=None, name="", v1=False, gate=0):
    assert lid not in by_id, lid
    d = {"id": lid, "kind": kind, "region": region, "group": group}
    if calling:
        d["calling"] = calling
    d.update({"name": name, "v1": v1, "x": pos[0], "y": pos[1], "at": list(at), "gate": gate})
    lamps.append(d)
    by_id[lid] = d
    return d


def group(gid, kind, name, callings, angle):
    groups.append({"id": gid, "kind": kind, "name": name, "callings": callings, "angle": angle})


def P(lid):
    d = by_id[lid]
    return d["x"], d["y"]


# ------------------------------------------------------------- load v1 ----
v1 = json.load(open(V1, encoding="utf-8"))
v1all = v1["lamps"]
assert len(v1all) == 360
V = {l["id"]: l for l in v1all if l["kind"] != "skill"}
assert len(V) == 288
ROADS = {r["id"]: r for r in v1["roads"]}
road_of_calling = {c: sorted([r for r in ROADS if ROADS[r]["calling"] == c], key=lambda r: ROAD_ANGLE[r]) for c in CALLINGS}
road_names = {r["id"]: r["name"] for r in v1["roads"]}


def v1lamp(lid, kind, region, group_, pos, at, calling=None, gate=0):
    l = V[lid]
    assert l["kind"] == kind or kind is None, (lid, l["kind"])
    return add(lid, l["kind"], region, group_, pos, at, calling, l["name"], True, gate)


def gate_for(kind, is_strike=False, is_stand=False):
    if is_strike:
        return 4
    if is_stand or kind == "blue":
        return 16
    if kind in ("notable", "link"):
        return 8
    return 0


# ----------------------------------------------------------------- roads ---
SPINE0, STEP = 400.0, 55.0
# hung slots in the road's local frame (u along the spine, v perpendicular; +v = outer side, away from the
# quarter's axis, -v = inner side).  O1/I1 sit 70 off the node; O2 is a second tier set 36 along and 145 out.
SLOT = {"O1": (0, 70), "O2": (36, 145), "I1": (0, -70), "I2": (36, -145)}
FAN = [(-48, 70), (0, 82), (48, 70)]          # mods fanned beyond the Strike / Stand
# node -> list of (what, slot)
ROAD_HANG = {1: [("rite1", "O1")],
             2: [("n1", "I1"), ("strike", "O1")],
             3: [("n2", "I1"), ("rite2", "O1")],
             4: [("n3", "O1"), ("link1", "O2")],
             5: [("n4", "I1"), ("rite3", "O1")],
             6: [("n5", "I1"), ("blue1", "O1"), ("stand", "O2")],
             7: [("n6", "I1"), ("blue2", "O1"), ("link2", "O2")],
             8: [("rite4", "O1")]}


def road_frame(rid):
    th = ROAD_ANGLE[rid]
    q = QUARTER[ROADS[rid]["calling"]]
    s = 1 if norm(th - q) < 180 else -1     # ccw road of the quarter: outer side is left
    return th, s


def road_pos(rid, k, u=0.0, v=0.0):
    """node k (0 = entry) of the spine; u along, v outer-positive."""
    th, s = road_frame(rid)
    r = SPINE0 + STEP * k + u
    ax, ay = dv(th)
    px, py = dv(th + 90 * s)
    return r * ax + v * px, r * ay + v * py


def build_road(rid):
    road = ROADS[rid]
    calling = road["calling"]
    entry = [l for l in V.values() if l["road"] == rid and l["kind"] == "entry"][0]
    spine = [f"{rid}.s{i}" for i in range(1, 8)]
    notables = sorted([l for l in V.values() if l["road"] == rid and l["kind"] == "notable"],
                      key=lambda l: spine.index(l["at"][0]))
    blues = sorted([l for l in V.values() if l["road"] == rid and l["kind"] == "blue"], key=lambda l: spine.index(l["at"][0]))
    strike_id, stand_id = f"{rid}.{road['strike']}", f"{rid}.{road['stand']}"
    mods = {sid: [l for l in V.values() if l["kind"] == "ultimateMod" and l["id"].startswith(sid + ".")] for sid in (strike_id, stand_id)}
    assert len(notables) == 5 and len(blues) == 2 and all(len(m) == 3 for m in mods.values())
    assert V[strike_id]["kind"] == V[stand_id]["kind"] == "ultimate"
    # entry's `at` is patched when the hearth is built (it hangs off p1 / p2)
    v1lamp(entry["id"], "entry", "road", rid, road_pos(rid, 0), [], calling)
    prev = entry["id"]
    nid = {1: spine[0]}
    for i in range(1, 10):
        sid = f"{rid}.s{i}"
        if i <= 7:
            v1lamp(sid, None, "road", rid, road_pos(rid, i), [prev], calling)
        else:
            add(sid, "small", "road", rid, road_pos(rid, i), [prev], calling)
        prev = sid
    names = {"rite1": None}
    notable_ids = [l["id"] for l in notables]
    for node, items in ROAD_HANG.items():
        sid = f"{rid}.s{node}"
        for what, slot in items:
            u, v = SLOT[slot]
            pos = road_pos(rid, node, u, v)
            if what.startswith("n") and len(what) == 2:
                idx = int(what[1]) - 1
                if idx < 5:
                    v1lamp(notable_ids[idx], "notable", "road", rid, pos, [sid], calling, 8)
                else:
                    add(f"{rid}.n6", "notable", "road", rid, pos, [sid], calling, gate=8)
            elif what.startswith("blue"):
                b = blues[int(what[-1]) - 1]
                v1lamp(b["id"], "blue", "road", rid, pos, [sid], calling, 16)
            elif what.startswith("rite"):
                add(f"{rid}.{what}", "rite", "road", rid, pos, [sid], calling)
            elif what.startswith("link"):
                add(f"{rid}.{what}", "link", "road", rid, pos, [sid], calling, gate=8)
            else:
                ult = strike_id if what == "strike" else stand_id
                v1lamp(ult, "ultimate", "road", rid, pos, [sid], calling, 4 if what == "strike" else 16)
                for (fu, fv), m in zip(FAN, mods[ult]):
                    mpos = road_pos(rid, node, u + fu, v + fv)
                    v1lamp(m["id"], "ultimateMod", "road", rid, mpos, [ult], calling, 4 if what == "strike" else 16)


# ---------------------------------------------------------------- bridge ---
def build_bridge(calling):
    gid = f"{calling}.bridge"
    ra, rb = road_of_calling[calling]          # ra = cw road, rb = ccw road
    q = QUARTER[calling]
    s1 = V[f"{gid}.s1"]
    assert s1["at"] == [f"{ra}.s4"] or s1["at"] == [f"{rb}.s4"]
    # v1 chain order starts from whichever road its s1 hangs on; make that road the cw one so the arc reads cw->ccw
    first, second = (ra, rb) if s1["at"] == [f"{ra}.s4"] else (rb, ra)
    br = [l for l in V.values() if l["road"] == gid]
    assert len(br) == 6
    ns = [l for l in br if l["kind"] == "notable"]
    n1 = [l for l in ns if l["at"] == [f"{gid}.s1"]][0]
    n2 = [l for l in ns if l["id"] != n1["id"]][0]
    blue = [l for l in br if l["kind"] == "blue"][0]
    # arc: s4's inner slot of each road is the bridge's s1 / s3 so both ends sit on the roads' inner I1 slot
    p_first = road_pos(first, 4, 0, -70)
    p_second = road_pos(second, 4, 0, -70)
    sgn = 1 if first == rb else -1               # side of the axis the first road is on
    r = math.hypot(*p_first)
    off = (math.degrees(math.atan2(p_first[1], p_first[0])) - q + 180) % 360 - 180
    e = abs(off)
    sg = 1 if off > 0 else -1
    angs = [q + sg * e, q + sg * e / 2, q, q - sg * e / 2, q - sg * e]
    pos = [pol(r, a) for a in angs]
    pos[0], pos[4] = p_first, p_second
    gt = 0
    v1lamp(f"{gid}.s1", None, "bridge", gid, pos[0], [f"{first}.s4"], calling)
    v1lamp(n1["id"], "notable", "bridge", gid, pos[1], [f"{gid}.s1"], calling, 8)
    v1lamp(f"{gid}.s2", None, "bridge", gid, pos[2], [n1["id"]], calling)
    v1lamp(blue["id"], "blue", "bridge", gid, pol(r + 80, q), [f"{gid}.s2"], calling, 16)
    v1lamp(n2["id"], "notable", "bridge", gid, pos[3], [f"{gid}.s2"], calling, 8)
    v1lamp(f"{gid}.s3", None, "bridge", gid, pos[4], [n2["id"], f"{second}.s4"], calling)
    add(f"{gid}.rite1", "rite", "bridge", gid, pol(r + 78, angs[1]), [n1["id"]], calling)
    add(f"{gid}.rite2", "rite", "bridge", gid, pol(r + 78, angs[3]), [n2["id"]], calling)


# ------------------------------------------------------------ ring cross ---
RING_R = 980.0
RING_T = [0.86, 0.56, 0.2, -0.2, -0.56, -0.86]
ring_mid = {}     # (cid) -> [(lamp id, angle)]


def build_ring(cid):
    cl = [l for l in V.values() if l["road"] == cid]
    assert len(cl) == 6
    a1, a2 = V[f"{cid}.a1"], V[f"{cid}.a2"]
    r1 = a1["at"][0].rsplit(".", 1)[0]
    r2 = [x for x in a2["at"] if not x.startswith(cid)][0].rsplit(".", 1)[0]
    th1, th2 = ROAD_ANGLE[r1], ROAD_ANGLE[r2]
    b = norm(round((th1 + (360 if th2 < th1 and th1 - th2 > 180 else 0) + th2) / 2)) if False else None
    # boundary: midpoint along the short way
    d = (th2 - th1 + 540) % 360 - 180
    b = norm(th1 + d / 2)
    ang = lambda t: b + (norm(th1 - b + 180) - 180) * t
    s1, n1, n2, s2 = f"{cid}.s1", None, None, f"{cid}.s2"
    ns = [l for l in cl if l["kind"] == "notable"]
    n1 = [l for l in ns if l["at"] == [s1]][0]
    n2 = [l for l in ns if l["id"] != n1["id"]][0]
    gid = cid
    v1lamp(f"{cid}.a1", None, "crossing", gid, pol(RING_R, ang(RING_T[0])), [f"{r1}.s9"])
    v1lamp(s1, None, "crossing", gid, pol(RING_R, ang(RING_T[1])), [f"{cid}.a1"])
    v1lamp(n1["id"], "notable", "crossing", gid, pol(RING_R, ang(RING_T[2])), [s1], None, 8)
    v1lamp(n2["id"], "notable", "crossing", gid, pol(RING_R, ang(RING_T[3])), [n1["id"]], None, 8)
    v1lamp(s2, None, "crossing", gid, pol(RING_R, ang(RING_T[4])), [n2["id"]])
    v1lamp(f"{cid}.a2", None, "crossing", gid, pol(RING_R, ang(RING_T[5])), [s2, f"{r2}.s9"])
    add(f"{cid}.rite1", "rite", "crossing", gid, pol(RING_R - 75, ang(0.2)), [n1["id"]])
    add(f"{cid}.rite2", "rite", "crossing", gid, pol(RING_R - 75, ang(-0.2)), [n2["id"]])
    add(f"{cid}.blue", "blue", "crossing", gid, pol(RING_R + 62, ang(0.45)), [n1["id"]], gate=16)
    add(f"{cid}.link", "link", "crossing", gid, pol(RING_R + 62, ang(-0.45)), [n2["id"]], gate=8)
    ring_mid[cid] = [(n1["id"], norm(ang(0.2))), (n2["id"], norm(ang(-0.2)))]
    return b, (r1, r2)


# ------------------------------------------------------- diagonals + ford ---
DIAG_R = {"a": 250.0, "s": 205.0, "n": 160.0, "rite": 118.0}
HUNG_OFF = 62.0


def build_diag(cid):
    name, ca, cb, ang = DIAG[cid]
    for side, calling, tag in (("1", ca, "a"), ("2", cb, "b")):
        q = QUARTER[calling]
        start = by_id[hearth_ids(calling)["start"]]
        a, s, n, rt = (f"{cid}.a{side}", f"{cid}.s{side}", f"{cid}.n{side}", f"{cid}.rite{side}")
        add(a, "attribute", "crossing", cid, pol(DIAG_R["a"], q), [start["id"]])
        add(s, "small", "crossing", cid, pol(DIAG_R["s"], q), [a])
        add(n, "notable", "crossing", cid, pol(DIAG_R["n"], q), [s], gate=8)
        add(rt, "rite", "crossing", cid, pol(DIAG_R["rite"], q), [n])
        # hung lamp: a little off the line, on the left of the ray as seen from the hearth looking in
        px, py = dv(q - 90)
        nx, ny = P(n)
        hx, hy = nx + HUNG_OFF * px, ny + HUNG_OFF * py
        if side == "1":
            add(f"{cid}.blue", "blue", "crossing", cid, (hx, hy), [n], gate=16)
        else:
            add(f"{cid}.link", "link", "crossing", cid, (hx, hy), [n], gate=8)


# the hearth start must exist before the diagonals; hearth build is split in two (starts first)
HEARTH_START_R = 300.0


def hearth_ids(calling):
    h = [l for l in V.values() if l["road"] == f"{calling}.hearth"]
    assert len(h) == 14
    start = [l for l in h if l["kind"] == "start"][0]["id"]
    forms = [l["id"] for l in h if l["kind"] == "form"]
    rx = [l["id"] for l in h if l["kind"] == "reflex"]
    ups = {r: [l["id"] for l in h if l["kind"] == "reflexUp" and l["at"] == [r]] for r in rx}
    fl = [l["id"] for l in h if l["kind"] == "flareLamp"]
    f1 = [x for x in fl if V[x]["at"] == [start]][0]
    f2 = [x for x in fl if x != f1][0]
    bl = [l["id"] for l in h if l["kind"] == "blue"]
    banked = [x for x in bl if V[x]["at"] == [f2]][0]
    unb = [x for x in bl if x != banked][0]
    assert len(forms) == 4 and len(rx) == 2 and V[unb]["at"] == [rx[1]]
    assert [len(ups[r]) for r in rx] == [2, 1]
    return dict(start=start, forms=forms, rx=rx, ups=ups, f1=f1, f2=f2, banked=banked, unb=unb)


# hearth cluster seed positions in the quarter frame (x outward along the axis from the start, y to the ccw side)
HSEED = {
    "forms": [(66, -50), (86, -17), (86, 17), (66, 50)],
    "r1": (-6, 100), "r1u": [(24, 150), (-40, 140)],
    "r2": (-6, -100), "r2u": [(-20, -150)], "unb": [(34, -150)],
    "f1": (-38, -52), "f2": (-82, -88), "banked": (-120, -50),
    "hand": [(-34, 52), (-66, 70), (-98, 88), (-130, 100)],
}
HEARTH_LOCAL = {}


def local_to_global(calling, x, y):
    q = QUARTER[calling]
    ax, ay = dv(q)
    px, py = dv(q + 90)
    return HEARTH_START_R * ax + x * ax + y * px, HEARTH_START_R * ay + x * ay + y * py


def global_to_local(calling, gx, gy):
    q = QUARTER[calling]
    ax, ay = dv(q)
    px, py = dv(q + 90)
    dx, dy = gx - HEARTH_START_R * ax, gy - HEARTH_START_R * ay
    return dx * ax + dy * ay, dx * px + dy * py


def build_hearth_starts():
    for c in CALLINGS:
        h = hearth_ids(c)
        v1lamp(h["start"], "start", "hearth", f"{c}.hearth", pol(HEARTH_START_R, QUARTER[c]), [], c)


def p_positions(calling):
    """p1 / p2 sit 0.62 of the way from the start to the cw / ccw road's entry."""
    ra, rb = road_of_calling[calling]
    s = P(f"{calling}.the_x") if False else None
    out = []
    st = pol(HEARTH_START_R, QUARTER[calling])
    for rid in (ra, rb):
        e = road_pos(rid, 0)
        out.append((st[0] + 0.62 * (e[0] - st[0]), st[1] + 0.62 * (e[1] - st[1])))
    return out


def build_hearth(calling, local):
    """local: dict id-suffix -> (x, y) quarter-frame positions, produced by the reaver relaxation."""
    gid = f"{calling}.hearth"
    h = hearth_ids(calling)
    st = h["start"]
    ra, rb = road_of_calling[calling]
    pp = p_positions(calling)
    for i, (rid, pos) in enumerate(zip((ra, rb), pp), 1):
        add(f"{gid}.p{i}", "small", "hearth", gid, pos, [st], calling)
        entry = [l["id"] for l in lamps if l["group"] == rid and l["kind"] == "entry"][0]
        by_id[entry]["at"] = [f"{gid}.p{i}"]
    G = lambda key: local_to_global(calling, *local[key])
    for i, f in enumerate(h["forms"]):
        v1lamp(f, "form", "hearth", gid, G(f"form{i}"), [st], calling)
    r1, r2 = h["rx"]
    v1lamp(r1, "reflex", "hearth", gid, G("r1"), [st], calling)
    for i, u in enumerate(h["ups"][r1]):
        v1lamp(u, "reflexUp", "hearth", gid, G(f"r1u{i}"), [r1], calling)
    v1lamp(r2, "reflex", "hearth", gid, G("r2"), [st], calling)
    v1lamp(h["ups"][r2][0], "reflexUp", "hearth", gid, G("r2u0"), [r2], calling)
    v1lamp(h["f1"], "flareLamp", "hearth", gid, G("f1"), [st], calling)
    v1lamp(h["f2"], "flareLamp", "hearth", gid, G("f2"), [h["f1"]], calling)
    v1lamp(h["unb"], "blue", "hearth", gid, G("unb"), [r2], calling, 16)
    v1lamp(h["banked"], "blue", "hearth", gid, G("banked"), [h["f2"]], calling, 16)
    prev = st
    for i in range(1, 5):
        add(f"{calling}.hand{i}", "hand", "hearth", gid, G(f"hand{i}"), [prev], calling)
        prev = f"{calling}.hand{i}"


def seed_local():
    s = {}
    for i, p in enumerate(HSEED["forms"]):
        s[f"form{i}"] = p
    s["r1"], s["r2"], s["f1"], s["f2"], s["banked"] = HSEED["r1"], HSEED["r2"], HSEED["f1"], HSEED["f2"], HSEED["banked"]
    for i, p in enumerate(HSEED["r1u"]):
        s[f"r1u{i}"] = p
    s["r2u0"] = HSEED["r2u"][0]
    s["unb"] = HSEED["unb"][0]
    for i, p in enumerate(HSEED["hand"], 1):
        s[f"hand{i}"] = p
    return s


def relax_hearth(obstacles, d_min=50.0, iters=1500):
    """Nudge the seeds (reaver quarter frame) until nothing is closer than d_min to anything."""
    seeds = seed_local()
    keys = list(seeds)
    pos = {k: list(v) for k, v in seeds.items()}
    for it in range(iters):
        force = {k: [0.0, 0.0] for k in keys}
        for k in keys:
            force[k][0] += 0.03 * (seeds[k][0] - pos[k][0])
            force[k][1] += 0.03 * (seeds[k][1] - pos[k][1])
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy) or 0.01
                if d < d_min:
                    f = 0.5 * (d_min - d) / d
                    force[a][0] += f * dx; force[a][1] += f * dy
                    force[b][0] -= f * dx; force[b][1] -= f * dy
            for ox, oy in obstacles:
                dx, dy = pos[a][0] - ox, pos[a][1] - oy
                d = math.hypot(dx, dy) or 0.01
                if d < d_min:
                    f = 1.0 * (d_min - d) / d
                    force[a][0] += f * dx; force[a][1] += f * dy
        for k in keys:
            pos[k][0] += force[k][0]
            pos[k][1] += force[k][1]
    return {k: (round(v[0], 1), round(v[1], 1)) for k, v in pos.items()}


# ------------------------------------------------------------------ paths ---
OLD_SPINE_R, OLD_HUNG_R = 1150.0, 1240.0
PATH_HANG = [["notable"], ["rite", "notable"], ["link"], ["blue"], ["notable", "rite"], ["notable"]]


def build_paths(anchors):
    ang = sorted(a for _, a, _ in PATHS)
    for pid, a0, pname in PATHS:
        i = ang.index(a0)
        gap = min((a0 - ang[i - 1]) % 360, (ang[(i + 1) % 10] - a0) % 360)
        half = min(14.0, gap / 2 - 1.5)
        gid = f"path.{pid}"
        sp = [a0 + half * (2 * k / 5 - 1) for k in range(6)]
        ends = []
        for e in (sp[0], sp[-1]):
            ends.append(min(anchors, key=lambda a: adiff(a[1], e) - (5 if a[2] == "mid" else 0)))
        assert ends[0][0] != ends[1][0], pid
        prev = None
        kinds_count = {"notable": 0, "rite": 0}
        for k in range(6):
            sid = f"{gid}.s{k + 1}"
            at = [ends[0][0]] if k == 0 else [prev]
            if k == 5:
                at = [prev, ends[1][0]]
            add(sid, "small", "oldroad", gid, pol(OLD_SPINE_R, sp[k]), at)
            prev = sid
        for k, items in enumerate(PATH_HANG):
            for j, kind in enumerate(items):
                off = 0.0 if len(items) == 1 else (-1 if j == 0 else 1) * 2.4
                if kind in kinds_count:
                    kinds_count[kind] += 1
                    lid = f"{gid}.{'n' if kind == 'notable' else 'rite'}{kinds_count[kind]}"
                else:
                    lid = f"{gid}.{kind}"
                add(lid, kind, "oldroad", gid, pol(OLD_HUNG_R, sp[k] + off), [f"{gid}.s{k + 1}"],
                    gate=16 if kind == "blue" else (8 if kind in ("notable", "link") else 0))


# ------------------------------------------------------------------- main ---
def main():
    for rid in ROAD_ANGLE:
        pass
    # groups (stable order)
    for c in CALLINGS:
        group(f"{c}.hearth", "hearth", f"{c.capitalize()} hearth", [c], QUARTER[c])
    for c in CALLINGS:
        for rid in road_of_calling[c]:
            group(rid, "road", road_names[rid], [c], ROAD_ANGLE[rid])
    for c in CALLINGS:
        group(f"{c}.bridge", "bridge", f"{c.capitalize()} bridge", [c], QUARTER[c])
    ring_ids = ["shambles", "night_road", "firebreak", "duelists_road"]
    ring_info = {}

    build_hearth_starts()
    for c in CALLINGS:
        pass
    # roads (hearth p's patch the entry ats)
    for c in CALLINGS:
        for rid in road_of_calling[c]:
            build_road(rid)
    for c in CALLINGS:
        build_bridge(c)
    for cid in ring_ids:
        b, rr = build_ring(cid)
        ring_info[cid] = (b, rr)
        group(cid, "crossing", RING_NAMES[cid], [ROADS[rr[0]]["calling"], ROADS[rr[1]]["calling"]], b)
    for cid in ("vigil", "poachers"):
        group(cid, "crossing", DIAG[cid][0], [DIAG[cid][1], DIAG[cid][2]], DIAG[cid][3])
    group("ford", "ford", "the Ford", [], 0)
    for pid, a0, pname in PATHS:
        group(f"path.{pid}", "oldroad", pname, [], a0)
    # hearth: relax the reaver quarter against everything placed so far, then turn it for the others
    build_diag_pending = True
    for cid in ("vigil", "poachers"):
        build_diag(cid)
    # ford
    add("ford.hub", "small", "ford", "ford", (0.0, 0.0), [f"{c}.rite{i}" for c in ("vigil", "poachers") for i in (1, 2)])
    add("ford.n1", "notable", "ford", "ford", (-72.0, 0.0), ["ford.hub"], gate=8)
    add("ford.n2", "notable", "ford", "ford", (72.0, 0.0), ["ford.hub"], gate=8)
    add("ford.unhoused", "blue", "ford", "ford", (0.0, 76.0), ["ford.hub"], gate=16)
    add("ford.s1", "small", "ford", "ford", (-122.0, 0.0), ["ford.n1"])
    add("ford.s2", "small", "ford", "ford", (122.0, 0.0), ["ford.n2"])
    # hearth obstacles (reaver frame): every placed lamp near the reaver start
    obst = [global_to_local("reaver", l["x"], l["y"]) for l in lamps]
    obst += [global_to_local("reaver", *p) for p in p_positions("reaver")]
    obst = [o for o in obst if math.hypot(o[0], o[1]) < 330 and not (abs(o[0]) < 1 and abs(o[1]) < 1)]
    local = relax_hearth(obst)
    for c in CALLINGS:
        build_hearth(c, local)
    # old roads: anchors = 8 roads' s9 and the ring crossings' middle (notable) lamps
    anchors = [(f"{rid}.s9", float(ROAD_ANGLE[rid]), "s9") for rid in ROAD_ANGLE]
    for cid in ring_ids:
        for lid, a in ring_mid[cid]:
            anchors.append((lid, a, "mid"))
    build_paths(anchors)
    # lamp order: by group order
    order = {g["id"]: i for i, g in enumerate(groups)}
    seq = {l["id"]: i for i, l in enumerate(lamps)}
    lamps.sort(key=lambda l: (order[l["group"]], seq[l["id"]]))
    for l in lamps:
        l["x"], l["y"] = round(l["x"] + 0.0, 1), round(l["y"] + 0.0, 1)
        l["x"] += 0.0
        l["y"] += 0.0
        if l["x"] == 0:
            l["x"] = 0.0
        if l["y"] == 0:
            l["y"] = 0.0
    check()
    write()
    preview()


def segdist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def check():
    from collections import Counter
    n = len(lamps)
    assert n == 574, n
    reg = Counter(l["region"] for l in lamps)
    assert reg == {"hearth": 80, "road": 256, "bridge": 32, "crossing": 60, "ford": 6, "oldroad": 140}, reg
    kind = Counter(l["kind"] for l in lamps)
    assert kind["blue"] == 45, kind["blue"]
    assert kind["hand"] == 16 and kind["rite"] == 72 and kind["link"] == 32, kind
    assert sum(1 for l in lamps if l["v1"]) == 288
    gc = Counter(l["group"] for l in lamps)
    for c in CALLINGS:
        assert gc[f"{c}.hearth"] == 20 and gc[f"{c}.bridge"] == 8
    for rid in ROAD_ANGLE:
        assert gc[rid] == 32, (rid, gc[rid])
    for cid in ("shambles", "night_road", "firebreak", "duelists_road", "vigil", "poachers"):
        assert gc[cid] == 10, (cid, gc[cid])
    assert gc["ford"] == 6
    for pid, _, _ in PATHS:
        assert gc[f"path.{pid}"] == 14
        pk = Counter(l["kind"] for l in lamps if l["group"] == f"path.{pid}")
        assert pk == {"small": 6, "notable": 4, "rite": 2, "link": 1, "blue": 1}, pk
    rk = Counter((l["region"], l["kind"]) for l in lamps if l["kind"] in ("rite", "link"))
    assert sum(v for (r, k), v in rk.items() if k == "rite" and r == "road") == 32
    assert sum(v for (r, k), v in rk.items() if k == "rite" and r == "bridge") == 8
    assert sum(v for (r, k), v in rk.items() if k == "rite" and r == "crossing") == 12
    assert sum(v for (r, k), v in rk.items() if k == "rite" and r == "oldroad") == 20
    assert sum(v for (r, k), v in rk.items() if k == "link" and r == "road") == 16
    assert sum(v for (r, k), v in rk.items() if k == "link" and r == "crossing") == 6
    assert sum(v for (r, k), v in rk.items() if k == "link" and r == "oldroad") == 10
    # edges
    ids = set(by_id)
    adj = {i: set() for i in ids}
    edges = []
    for l in lamps:
        for a in l["at"]:
            assert a in ids, (l["id"], a)
            adj[l["id"]].add(a); adj[a].add(l["id"])
            edges.append((a, l["id"]))
    seen, todo = set(), [f"{c}.{[x for x in V if x.startswith(c + '.') and V[x]['kind'] == 'start'][0].split('.', 1)[1]}" for c in CALLINGS]
    todo = [l["id"] for l in lamps if l["kind"] == "start"]
    assert len(todo) == 4
    seen.update(todo)
    while todo:
        x = todo.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y); todo.append(y)
    assert seen == ids, sorted(ids - seen)[:10]
    # spacing
    pairs = []
    for i, a in enumerate(lamps):
        for b in lamps[i + 1:]:
            d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
            if d < 60:
                pairs.append((d, a["id"], b["id"]))
    pairs.sort()
    mind = pairs[0][0] if pairs else 999
    # edge clearance
    bad = []
    for a, b in edges:
        pa, pb = P(a), P(b)
        for l in lamps:
            if l["id"] in (a, b):
                continue
            d = segdist((l["x"], l["y"]), pa, pb)
            if d < 15:
                bad.append((round(d, 1), a, b, l["id"]))
    bad.sort()
    rmax = max(math.hypot(l["x"], l["y"]) for l in lamps)
    hr = max(math.hypot(l["x"] - (HEARTH_START_R * math.cos(math.radians(QUARTER[l["calling"]]))),
                        l["y"] - (HEARTH_START_R * math.sin(math.radians(QUARTER[l["calling"]]))))
             for l in lamps if l["region"] == "hearth")
    print("lamps", n, dict(reg))
    print("kinds", dict(sorted(kind.items())))
    print(f"min lamp distance {mind:.1f}  (need >= 38); outer radius {rmax:.0f}; hearth reach {hr:.0f}")
    for p in pairs[:10]:
        if p[0] < 38:
            print("  CLOSE", p)
    print("edges", len(edges), " edge-near-lamp violations:", len(bad))
    for b in bad[:15]:
        print("  EDGE", b)
    assert mind >= 38, "spacing"
    return bad


def write():
    out = {"version": 2, "coords": "board units, y up, the Ford at (0,0)", "groups": groups, "lamps": lamps}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", OUT)


COLORS = {"blue": "#3d7bff", "rite": "#b05cff", "link": "#2ee6e6", "hand": "#ff9a2e", "notable": "#e8c13a",
          "small": "#8a8a8a", "attribute": "#8a8a8a", "entry": "#ffffff", "start": "#ffffff",
          "ultimate": "#ff3b3b", "ultimateMod": "#a02828", "form": "#7fc77f", "reflex": "#c9a27a",
          "reflexUp": "#a8845f", "flareLamp": "#ff7f50"}


def preview():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(os.path.dirname(PNG), exist_ok=True)
    fig = plt.figure(figsize=(16, 16), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    fig.patch.set_facecolor("#0b0d12"); ax.set_facecolor("#0b0d12")
    for l in lamps:
        for a in l["at"]:
            ax.plot([by_id[a]["x"], l["x"]], [by_id[a]["y"], l["y"]], color="#555a66", lw=0.7, zorder=1)
    for kind in COLORS:
        pts = [l for l in lamps if l["kind"] == kind]
        size = {"notable": 70, "blue": 46, "ultimate": 60, "start": 60, "entry": 40}.get(kind, 24)
        ax.scatter([l["x"] for l in pts], [l["y"] for l in pts], s=size, c=COLORS[kind], zorder=3, linewidths=0)
    for g in groups:
        pts = [l for l in lamps if l["group"] == g["id"]]
        cx, cy = sum(l["x"] for l in pts) / len(pts), sum(l["y"] for l in pts) / len(pts)
        ax.text(cx, cy, g["name"], color="#d8dce6", fontsize=7.5, ha="center", va="center", zorder=5,
                bbox=dict(boxstyle="round,pad=0.15", fc="#0b0d12", ec="none", alpha=0.65))
    ax.set_xlim(-1360, 1360); ax.set_ylim(-1360, 1360); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(PNG, facecolor=fig.get_facecolor())
    print("wrote", PNG)


if __name__ == "__main__":
    main()
