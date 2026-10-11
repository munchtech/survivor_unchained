"""Builds godot/data/content/lamps.json: the Lamps board (docs/design/CLASSES.md §2-3).

This script is the board's source: edit here, run it, commit both. It lays every quarter
out in the same shape (§2.2), so the joins, the gates and the counts stay true:

  hearth (14): the start lamp (the dash form) with the form's four lamps; two reflexes and
               their upgrades; two Flare lamps; the calling's blue lamp and Banked Flame.
  road (32):   entry - s1 - s2 - ... - s7 (seven small lamps on a spine);
               the three skills' lamps hang from s1, s3, s5; notables from s2..s6;
               the blue lamps from s6 and s7; the Strike from s2 and the Stand from s6,
               each with its three modifiers.
  bridge (6):  A.s4 - small - notable - small(+blue) - notable - small - B.s4.
  crossing (6): R.s7 - attribute - small - notable - notable - small - attribute - Q.s7.

Phase (docs/design/CLASSES.md §7): 1 works now; 2 waits on the staged Flares; 4 on the new
grips (heavy blows, the greatsword); 5 on the new skills (and their tags' mechanics).

Run: python tools/classes/lamps_build.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "godot", "data", "content", "lamps.json"))

lamps, roads, flares = [], [], []


# ---------------------------------------------------------------- effects --

def M(stat, v, kind="inc", when=None, price=False, phase=1, skill=None):
    e = {"do": "mod", "stat": stat, "mod": kind, "value": v}
    if when: e["when"] = when
    if price: e["price"] = True
    if skill: e["skill"] = skill
    if phase != 1: e["phase"] = phase
    return e


def A(attr, n=2):
    return {"do": "attr", "attr": attr, "value": n}


def R(rule, phase=1, skill=None, tags=None, status=None, **args):
    e = {"do": "rule", "rule": rule}
    if args: e["args"] = args
    if skill: e["skill"] = skill
    if tags: e["tags"] = tags.split(",")
    if status: e["status"] = status
    if phase != 1: e["phase"] = phase
    return e


def F(art, facet):
    return {"do": "facet", "art": art, "facet": facet}


def FORM(art, wait):
    return {"do": "form", "art": art, "wait": wait}


def RX(art, trigger, wait, **args):
    e = {"do": "reflex", "art": art, "trigger": trigger, "wait": wait}
    if args: e["args"] = args
    return e


def FL(flare):
    return {"do": "flare", "flare": flare}


def FM(flare, rule, phase=2, **args):
    e = {"do": "flareMod", "flare": flare, "rule": rule}
    if args: e["args"] = args
    if phase != 1: e["phase"] = phase
    return e


def lamp(id, name, kind, region, text, effects, at=(), calling=None, road=None, gate=0, feeds=()):
    lamps.append({k: v for k, v in {
        "id": id, "name": name, "kind": kind, "region": region, "calling": calling, "road": road,
        "at": list(at), "feeds": list(feeds), "gate": gate, "text": text, "effects": effects,
    }.items() if v not in (None, [], 0) or k in ("effects",)})
    return id


def slug(s):
    out = "".join(c.lower() if c.isalnum() else "_" for c in s.replace("'", ""))
    while "__" in out: out = out.replace("__", "_")
    return out.strip("_")


# ----------------------------------------------------------------- layout --

def hearth(calling, start, form, forms, rx1, rx1_ups, rx2, rx2_ups, flare_lamps, blue):
    """start: (name, text); form: (art, wait); forms: four (facet, name, text);
    rx: (name, text, art, trigger, wait, args); ups: (facet or rule effect, name, text);
    flare_lamps: two (name, text, effect); blue: (name, text, effects)."""
    g = f"{calling}.hearth"
    s = lamp(f"{calling}.{slug(start[0])}", start[0], "start", "hearth", start[1], [FORM(*form)], calling=calling, road=g)
    for facet, name, text in forms:
        lamp(f"{calling}.{slug(name)}", name, "form", "hearth", text, [F(form[0], facet)], at=[s], calling=calling, road=g)
    r1 = lamp(f"{calling}.{slug(rx1[0])}", rx1[0], "reflex", "hearth", rx1[1], [RX(rx1[2], rx1[3], rx1[4], **rx1[5])], at=[s], calling=calling, road=g)
    for eff, name, text in rx1_ups:
        lamp(f"{calling}.{slug(name)}", name, "reflexUp", "hearth", text, [eff], at=[r1], calling=calling, road=g)
    r2 = lamp(f"{calling}.{slug(rx2[0])}", rx2[0], "reflex", "hearth", rx2[1], [RX(rx2[2], rx2[3], rx2[4], **rx2[5])], at=[s], calling=calling, road=g)
    for eff, name, text in rx2_ups:
        lamp(f"{calling}.{slug(name)}", name, "reflexUp", "hearth", text, [eff], at=[r2], calling=calling, road=g)
    f1 = lamp(f"{calling}.{slug(flare_lamps[0][0])}", flare_lamps[0][0], "flareLamp", "hearth", flare_lamps[0][1], [flare_lamps[0][2]], at=[s], calling=calling, road=g)
    f2 = lamp(f"{calling}.{slug(flare_lamps[1][0])}", flare_lamps[1][0], "flareLamp", "hearth", flare_lamps[1][1], [flare_lamps[1][2]], at=[f1], calling=calling, road=g)
    lamp(f"{calling}.{slug(blue[0])}", blue[0], "blue", "hearth", blue[1], blue[2], at=[r2], calling=calling, road=g, gate=6)
    lamp(f"{calling}.banked_flame", "Banked Flame", "blue", "hearth", "Hold two Flares. Each fills 30% slower.",
         [R("flare.banked", charges=2, slower=0.3)], at=[f2], calling=calling, road=g, gate=6)
    return s


def road(calling, start, rid, name, line, entry, smalls, skills, notables, blues, strike, stand, grip=None):
    """entry: (name, text, effects); smalls: seven (text, effects) or (name, text, effects);
    skills: three (skill_id, [three (name, text, effects)]); notables: five (name, text, effects, feeds);
    blues: two (name, text, effects); strike/stand: (flare_id, name, [three (name, text, effect)])."""
    assert len(smalls) == 7 and len(skills) == 3 and len(notables) == 5 and len(blues) == 2
    e = lamp(f"{rid}.{slug(entry[0])}", entry[0], "entry", "road", entry[1], entry[2], at=[start], calling=calling, road=rid,
             feeds=entry[3] if len(entry) > 3 else ())
    spine, prev = [], e
    for i, sm in enumerate(smalls, 1):
        nm, text, effs = (sm if len(sm) == 3 else (None, sm[0], sm[1]))
        kind = "attribute" if any(x["do"] == "attr" for x in effs) else "small"
        sid = f"{rid}.s{i}"
        lamp(sid, nm or "", kind, "road", text, effs, at=[prev], calling=calling, road=rid)
        spine.append(sid)
        prev = sid
    for k, (skill, three) in enumerate(skills):
        hang = spine[[0, 2, 4][k]]
        for nm, text, effs in three:
            lamp(f"{rid}.{skill}.{slug(nm)}", nm, "skill", "road", text, effs, at=[hang], calling=calling, road=rid, feeds=[skill])
    for k, (nm, text, effs, feeds) in enumerate(notables):
        lamp(f"{rid}.{slug(nm)}", nm, "notable", "road", text, effs, at=[spine[1 + k]], calling=calling, road=rid, gate=6, feeds=feeds)
    for k, (nm, text, effs) in enumerate(blues):
        lamp(f"{rid}.{slug(nm)}", nm, "blue", "road", text, effs, at=[spine[5 + k]], calling=calling, road=rid, gate=12)
    for (fid, fname, mods), hang, gate in ((strike, spine[1], 3), (stand, spine[5], 12)):
        u = lamp(f"{rid}.{fid}", fname, "ultimate", "road", f"Learn the Flare {fname}.", [FL(fid)], at=[hang], calling=calling, road=rid, gate=gate)
        for nm, text, eff in mods:
            lamp(f"{rid}.{fid}.{slug(nm)}", nm, "ultimateMod", "road", text, [eff], at=[u], calling=calling, road=rid, gate=gate)
    roads.append({"id": rid, "calling": calling, "name": name, "line": line, "grip": grip,
                  "skills": [s for s, _ in skills], "strike": strike[0], "stand": stand[0]})
    return spine


def bridge(calling, a_spine, b_spine, smalls, n1, blue, n2):
    """smalls: three (text, effects); n1, n2: (name, text, effects, feeds); blue: (name, text, effects)."""
    g = f"{calling}.bridge"
    s1 = lamp(f"{g}.s1", "", kind_of(smalls[0][1]), "bridge", smalls[0][0], smalls[0][1], at=[a_spine[3]], calling=calling, road=g)
    a = lamp(f"{g}.{slug(n1[0])}", n1[0], "notable", "bridge", n1[1], n1[2], at=[s1], calling=calling, road=g, feeds=n1[3])
    s2 = lamp(f"{g}.s2", "", kind_of(smalls[1][1]), "bridge", smalls[1][0], smalls[1][1], at=[a], calling=calling, road=g)
    lamp(f"{g}.{slug(blue[0])}", blue[0], "blue", "bridge", blue[1], blue[2], at=[s2], calling=calling, road=g, gate=3)
    b = lamp(f"{g}.{slug(n2[0])}", n2[0], "notable", "bridge", n2[1], n2[2], at=[s2], calling=calling, road=g, feeds=n2[3])
    lamp(f"{g}.s3", "", kind_of(smalls[2][1]), "bridge", smalls[2][0], smalls[2][1], at=[b, b_spine[3]], calling=calling, road=g)


def crossing(cid, a_spine, b_spine, attrs, smalls, n1, n2):
    """attrs: two (text, effects); smalls: two (text, effects); n: (name, text, effects, feeds)."""
    a1 = lamp(f"{cid}.a1", "", "attribute", "crossing", attrs[0][0], attrs[0][1], at=[a_spine[6]], road=cid)
    c1 = lamp(f"{cid}.s1", "", "small", "crossing", smalls[0][0], smalls[0][1], at=[a1], road=cid)
    x = lamp(f"{cid}.{slug(n1[0])}", n1[0], "notable", "crossing", n1[1], n1[2], at=[c1], road=cid, feeds=n1[3])
    y = lamp(f"{cid}.{slug(n2[0])}", n2[0], "notable", "crossing", n2[1], n2[2], at=[x], road=cid, feeds=n2[3])
    c2 = lamp(f"{cid}.s2", "", "small", "crossing", smalls[1][0], smalls[1][1], at=[y], road=cid)
    lamp(f"{cid}.a2", "", "attribute", "crossing", attrs[1][0], attrs[1][1], at=[c2, b_spine[6]], road=cid)


def kind_of(effs):
    return "attribute" if any(x["do"] == "attr" for x in effs) else "small"


def flare(fid, name, calling, rid, kind, length, radius, blows, power, school, tags, text, guard=None, guard_value=0):
    f = {"id": fid, "name": name, "calling": calling, "road": rid, "kind": kind, "length": length, "radius": radius,
         "blows": blows, "power": power, "school": school, "tags": tags, "text": text}
    if guard: f["guard"], f["guardValue"] = guard, guard_value
    flares.append(f)


exec(open(os.path.join(HERE, "lamps_quarters.py"), encoding="utf-8").read())

data = {"story": ["hollow_by_night", "roost_raid", "dig_boils", "vault_opened"], "roads": roads, "flares": flares, "lamps": lamps}
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)
    fh.write("\n")
print(f"{len(lamps)} lamps, {len(roads)} roads, {len(flares)} flares -> {OUT}")
