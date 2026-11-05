"""Checks godot/data/content/skill_lamps.json (docs/design/ONE_BUILD.md 4) against the one build's rules.

Run from the repo root: python tools/classes/skill_lamps_check.py
Prints one line: OK, or the count of problems (then each problem). Exit code 1 on any problem.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "godot" / "data" / "content"
KINDS = {"element", "shape", "trigger", "cost", "calling"}
ENGINES = {"built", "rule", "new"}
# A line that is only a percent: "+10% damage", "8% shorter cooldown", "Dawnpulse reaches 20% wider."
STAT = r"(?:damage|area|cooldown|speed|reach|size|range|radius|duration|harder|wider|larger|faster|longer|shorter|further|farther|more|less)"
ONLY_PERCENT = re.compile(
    r"^\s*(?:[A-Z][\w' -]*?\s+(?:is|are|has|gets|deals|strikes|reaches|swings|hits|lasts|comes|runs|flies)\s+)?"
    r"[+-]?\d+(?:\.\d+)?%\s+(?:" + STAT + r"\s*){1,2}(?:\s+(?:damage|area|cooldown|speed|reach|size|range))?\s*\.?\s*$", re.I)
# A barrier or a mend too small to feel (the judge, 5 Nov): under 2% of health an event, unless the line holds
# a cap of 2% or more ("1% for each thing it strikes, 8% at most"; "0.5%, 15% held at most").
SMALL = re.compile(r"(?:barrier of|mends you) (\d+(?:\.\d+)?)% of health")
CAP = re.compile(r"(\d+(?:\.\d+)?)%(?: held)? at most")
# Stones: the wall answers at six and the count starts over, so a line can never ask for six or more held.
STONES = re.compile(r"(\d+) or more Stones")
BRITISH = re.compile(r"\b(armour|colour|honour|favour|behaviour|grey|metre|centre|defence|plough|whilst|judgement|towards|ardour|valour|splendour)\b", re.I)


def main():
    probs = []
    txt = (CONTENT / "skill_lamps.json").read_text(encoding="utf-8")
    d = json.loads(txt)  # strict JSON: no comments
    for k in ("about", "rules", "keywords", "skills", "lamps", "unions"):
        if k not in d:
            probs.append(f"missing top-level '{k}'")
    costs = d["rules"]["costs"]
    heads = {h["id"]: h for h in d["skills"]}
    v2 = json.loads((CONTENT / "lamps_v2.json").read_text(encoding="utf-8"))
    banned = {l["name"] for l in v2["lamps"] if l.get("calling") == "warden" and l.get("name")} | {f["name"] for f in v2["flares"]}

    for sid, h in heads.items():
        ids = [s["id"] for s in h["strands"]]
        if len(ids) != 3 or len(set(ids)) != 3:
            probs.append(f"{sid}: needs 3 distinct strands")
        if h.get("suggested") not in ids:
            probs.append(f"{sid}: suggested '{h.get('suggested')}' is not a strand")
        if set(h.get("opens", {})) != {"sunderer", "bulwark"}:
            probs.append(f"{sid}: opens needs sunderer and bulwark")
        for s in h["strands"]:
            if s.get("kind") not in KINDS:
                probs.append(f"{sid}.{s['id']}: strand kind '{s.get('kind')}'")

    seen_ids, seen_names = set(), {}
    by = {}
    for l in d["lamps"]:
        lid, sk, st, n = l["id"], l["skill"], l["strand"], l["n"]
        by.setdefault(sk, []).append(l)
        if lid in seen_ids:
            probs.append(f"{lid}: duplicate id")
        seen_ids.add(lid)
        if lid != f"{sk}.{st}.{n}":
            probs.append(f"{lid}: id is not <skill>.<strand>.<n>")
        if sk not in heads or st not in [s["id"] for s in heads[sk]["strands"]]:
            probs.append(f"{lid}: unknown skill or strand")
        want_parent = None if n == 1 else f"{sk}.{st}.{n - 1}"
        if l.get("parent") != want_parent:
            probs.append(f"{lid}: parent {l.get('parent')} (want {want_parent})")
        if l.get("turn") != (n == 4):
            probs.append(f"{lid}: turn must be true only at n=4")
        want_cost = costs["turn"] if n == 4 else costs["leadIn"]
        if l.get("cost") != want_cost:
            probs.append(f"{lid}: cost {l.get('cost')} (want {want_cost})")
        if l.get("kind") not in KINDS:
            probs.append(f"{lid}: kind '{l.get('kind')}'")
        if l.get("engine") not in ENGINES:
            probs.append(f"{lid}: engine '{l.get('engine')}'")
        if not l.get("effects"):
            probs.append(f"{lid}: no effects")
        for k in ("name", "rule", "from"):
            if not l.get(k):
                probs.append(f"{lid}: missing {k}")
        check_text(lid, l["name"], l["rule"], banned, seen_names, probs)

    for sid in heads:
        lamps = by.get(sid, [])
        if len(lamps) != 12:
            probs.append(f"{sid}: {len(lamps)} lamps (want 12)")
        for s in heads[sid]["strands"]:
            ns = sorted(l["n"] for l in lamps if l["strand"] == s["id"])
            if ns != [1, 2, 3, 4]:
                probs.append(f"{sid}.{s['id']}: lamps n={ns} (want 1-4)")

    turns = {l["id"] for l in d["lamps"] if l["n"] == 4}
    for u in d["unions"]:
        uid = u["id"]
        if uid in seen_ids:
            probs.append(f"{uid}: duplicate id")
        seen_ids.add(uid)
        a, b = u["skills"]
        if a not in heads or b not in heads or a == b:
            probs.append(f"{uid}: needs two different known skills")
        par = u.get("parent", [])
        if len(par) != 2 or any(not set(p) <= turns or not p for p in par):
            probs.append(f"{uid}: parent must be two lists of Turn ids")
        elif not all(t.startswith(sk + ".") for p, sk in zip(par, (a, b)) for t in p):
            probs.append(f"{uid}: parent lists must be each skill's own Turns")
        if u.get("cost") != costs["union"] or u.get("costFrom") != {a: 1, b: 1}:
            probs.append(f"{uid}: cost must be {costs['union']}, one from each skill")
        if u.get("engine") not in ENGINES:
            probs.append(f"{uid}: engine '{u.get('engine')}'")
        check_text(uid, u["name"], u["rule"], banned, seen_names, probs)

    kw = d.get("keywords", {})
    if not kw or not all(isinstance(v, str) and v and "\n" not in v for v in kw.values()):
        probs.append("keywords: needs one line for each keyword")
    nl = len(d["lamps"])
    if probs:
        print(f"skill_lamps_check: {len(probs)} problem(s) in {len(heads)} skills, {nl} lamps, {len(d['unions'])} unions")
        for p in probs:
            print("  " + p)
        return 1
    print(f"skill_lamps_check: OK: {len(heads)} skills, {nl} lamps, {len(d['unions'])} unions; parents, Turns, costs, kinds, unique ids and names, no bare-percent line, no barrier or mend too small to feel, blow-fed barriers bounded, Stones reachable, keywords")
    return 0


def check_text(lid, name, rule, banned, seen_names, probs):
    if name in seen_names:
        probs.append(f"{lid}: name '{name}' already used by {seen_names[name]}")
    seen_names.setdefault(name, lid)
    if name in banned:
        probs.append(f"{lid}: name '{name}' is a warden lamp in lamps_v2.json or a Flare")
    if "\n" in rule:
        probs.append(f"{lid}: rule is more than one line")
    if not re.search(r"\d", rule):
        probs.append(f"{lid}: rule has no number")
    if ONLY_PERCENT.match(rule):
        probs.append(f"{lid}: rule is only a percent: '{rule}'")
    for m in SMALL.finditer(rule):
        if float(m.group(1)) < 2 and not any(float(x) >= 2 for x in CAP.findall(rule)):
            probs.append(f"{lid}: {m.group(1)}% of health is too small to feel (2% or more, or a cap of 2% or more)")
    if re.search(r"gives (?:you )?a barrier|mends you", rule) and re.search(r"blows? on you|blow reaches you|strikes you|\b[Aa] rebuke\b|each rebuke", rule) \
            and not re.search(r"at most every|as often as every|held at most", rule):
        probs.append(f"{lid}: a barrier or mend from blows on her needs 'at most every' or 'held at most'")
    for m in STONES.finditer(rule):
        if int(m.group(1)) >= 6:
            probs.append(f"{lid}: {m.group(1)} or more Stones can never be held (the wall answers at six)")
    if BRITISH.search(rule) or BRITISH.search(name):
        probs.append(f"{lid}: British spelling in '{name}: {rule}'")


if __name__ == "__main__":
    sys.exit(main())
