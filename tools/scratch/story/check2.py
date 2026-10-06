"""Static checks over Survivor Unchained's story content (read-only).

Dialogue graph: broken goto/next/entry targets, unreachable nodes, dead-end
nodes, duplicate 'once' keys. World language: facts, knowledge, quest
entries, history events, npc flags and items, written vs read, across the
content JSON and the C# that embeds the same language.
"""
import json, re, os, glob, collections

ROOT = r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a473fbc4762172b02/godot"
C = ROOT + "/data/content/"
load = lambda f: json.load(open(C + f, encoding="utf8"))
dlg = load("dialogue.json"); quests = load("quests.json"); items = load("items.json")["items"]
arch = load("archetypes.json")

out = []
def say(*a): out.append(" ".join(str(x) for x in a))

# ---------------------------------------------------------------- graph
say("## Dialogue graph")
for cid, cv in dlg.items():
    nodes = cv["nodes"]
    for e in cv["entry"]:
        if e["node"] not in nodes: say(f"BROKEN entry {cid}: -> {e['node']}")
    reach = set(); stack = [e["node"] for e in cv["entry"] if e["node"] in nodes]
    while stack:
        n = stack.pop()
        if n in reach: continue
        reach.add(n)
        nd = nodes[n]
        if nd.get("next"):
            if nd["next"] not in nodes: say(f"BROKEN next {cid}.{n} -> {nd['next']}")
            else: stack.append(nd["next"])
        for ch in nd.get("choices") or []:
            g = ch.get("goto")
            if g:
                if g not in nodes: say(f"BROKEN goto {cid}.{n} -> {g}")
                else: stack.append(g)
    for n in nodes:
        if n not in reach: say(f"UNREACHABLE node {cid}.{n}")
    onces = collections.Counter()
    for n, nd in nodes.items():
        if not nd.get("choices") and not nd.get("next"):
            pass  # click-to-close; fine
        for ch in nd.get("choices") or []:
            if ch.get("once"): onces[(ch["once"], json.dumps(ch.get("text")))] += 1
            if ch.get("goto") == n and not ch.get("effects"):
                say(f"SELF-LOOP {cid}.{n}: choice {str(ch.get('text'))[:50]!r} returns to the same node")
    # entry order shadowing: an unconditional entry before others
    for i, e in enumerate(cv["entry"][:-1]):
        if not e.get("when"): say(f"SHADOWED entries in {cid}: unconditional entry #{i} hides the rest")
    # duplicated entry conditions
    seen = {}
    for e in cv["entry"]:
        k = json.dumps(e.get("when"), sort_keys=True)
        if k in seen and k != "null": say(f"DUPLICATE entry condition in {cid}: {k} (nodes {seen[k]}, {e['node']})")
        seen[k] = e["node"]

# ---------------------------------------------------------------- world language
texts = {}
for f in glob.glob(C + "*.json"): texts[os.path.basename(f)] = open(f, encoding="utf8").read()
for f in glob.glob(ROOT + "/logic/**/*.cs", recursive=True) + glob.glob(ROOT + "/src/**/*.cs", recursive=True):
    texts[os.path.relpath(f, ROOT).replace("\\", "/")] = open(f, encoding="utf8").read()

W = collections.defaultdict(lambda: collections.defaultdict(set))  # kind -> key -> files written
R = collections.defaultdict(lambda: collections.defaultdict(set))  # kind -> key -> files read
def w(kind, k, f): W[kind][k].add(f)
def r(kind, k, f): R[kind][k].add(f)

for f, t in texts.items():
    # facts
    for m in re.finditer(r'"(?:set|add)"\s*:\s*\{([^{}]*)\}', t):
        for k in re.findall(r'"([\w.]+)"\s*:', m.group(1)): w("fact", k, f)
    for k in re.findall(r'Facts\["([\w.]+)"\]\s*=', t): w("fact", k, f)
    for k in re.findall(r'"fact"\s*:\s*"([\w.]+)"', t): r("fact", k, f)
    for k in re.findall(r'\b(?:F|Fact|Num)\((?:c, *)?"([\w.]+)"\)', t): r("fact", k, f)
    for k in re.findall(r'\bf\["([\w.]+)"\]\s*=', t): w("fact", k, f)
    for k in re.findall(r'TurnHostile\("([\w.]+)"', t): w("fact", k, f)
    for m in re.finditer(r'"(?:set|add)"\s*:\s*\{\s*"([\w.]+)"\s*:\s*\{\{', t): w("fact", m.group(1), f)
    for k in re.findall(r'FactKey\s*=\s*"([\w.]+)"', t): r("fact", k, f)
    for k in re.findall(r'\{fact:([\w.]+)\}', t): r("fact", k, f)
    # knowledge
    for m in re.finditer(r'"learn"\s*:\s*(\[[^\]]*\]|"[^"]+")', t):
        for k in re.findall(r'"([\w.]+)"', m.group(1)): w("know", k, f)
    for k in re.findall(r'"(?:knows|notKnows)"\s*:\s*"([\w.]+)"', t): r("know", k, f)
    for k in re.findall(r'\bKnows\("([\w.]+)"\)', t): r("know", k, f)
    for k in re.findall(r'Knows\s*=\s*"([\w.]+)"', t): r("know", k, f)
    # quest entries
    for m in (re.finditer(r'"quest"\s*:\s*\{([^{}]*)\}', t) if not f.endswith(".json") else []):
        body = m.group(1)
        qid = re.search(r'"id"\s*:\s*"(\w+)"', body); ent = re.search(r'"entry"\s*:\s*"([\w.]+)"', body)
        if qid and ent:
            # cond vs change cannot be told apart by shape alone; record both and sort it out below
            w("entry", f"{qid.group(1)}/{ent.group(1)}", f)
    for m in re.finditer(r'"entry"\s*:\s*"\{\{\(\w+ \? "(\w+)" : "(\w+)"\)\}\}"', t):
        w("entry", f"beasts/{m.group(1)}", f); w("entry", f"beasts/{m.group(2)}", f)
    for a, b in re.findall(r'\b(?:Quest|Q)\("(\w+)",\s*"([\w.]+)"\)', t): r("entry", f"{a}/{b}", f)
    # history
    for k in re.findall(r'"history"\s*:\s*\{\s*"id"\s*:\s*"(\w+)"', t): w("hist", k, f)
    for k in re.findall(r'Hist\("(\w+)"', t): w("hist", k, f)
    for k in re.findall(r'"history"\s*:\s*"(\w+)"', t): r("hist", k, f)
    for k in re.findall(r'"event"\s*:\s*"(\w+)"', t): r("hist", k, f)
    # npc flags
    for m in re.finditer(r'"npcFlag"\s*:\s*\{([^{}]*)\}', t):
        body = m.group(1); key = re.search(r'"key"\s*:\s*"([\w:.]+)"', body); npc = re.search(r'"npc"\s*:\s*"(\w+)"', body)
        if key and npc: (w if '"value"' in body else r)("flag", f"{npc.group(1)}/{key.group(1)}", f)
    # items
    for k in re.findall(r'"(?:give)"\s*:\s*"(\w+)"', t): w("item", k, f)
    for k in re.findall(r'"(?:hasItem|take)"\s*:\s*"(\w+)"', t): r("item", k, f)
    for k in re.findall(r'\b(?:HasItem|Has)\("(\w+)"\)', t): r("item", k, f)
    for k in re.findall(r'Loot\(PickupKind\.(?:Item|Material),\s*"(\w+)"', t): w("item", k, f)

# quest-entry conditions in dialogue: walk JSON properly to split cond from change
def walk_cond(c, f):
    if not isinstance(c, dict): return
    if "quest" in c and isinstance(c["quest"], dict) and c["quest"].get("entry"):
        r("entry", f"{c['quest']['id']}/{c['quest']['entry']}", f)
    for k in ("all", "any"):
        for x in c.get(k) or []: walk_cond(x, f)
    if c.get("not"): walk_cond(c["not"], f)
def walk_any(o, f, key=None):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("when", "show", "if") and isinstance(v, dict) and "text" not in v: walk_cond(v, f); continue
            if k == "quest" and isinstance(v, dict) and v.get("entry"): w("entry", f"{v['id']}/{v['entry']}", f)
            walk_any(v, f, k)
    elif isinstance(o, list):
        for x in o: walk_any(x, f, key)
for fn in ("dialogue.json", "concerns.json", "rules.json", "folk.json", "shops.json"):
    walk_any(load(fn), fn)
# 'quest' conds in C# literal JSON inside Test("""...""") are rare; Objectives use h.Entry("x") for beasts/caravan
for f, t in texts.items():
    for k in re.findall(r'\bh\.Entry\("([\w.]+)"\)', t): r("entry", f"?/{k}", f)

# backgrounds grant knowledge
for b in arch["backgrounds"].values():
    for k in b.get("knowledge", []): w("know", k, "archetypes.json(background)")

# quest entries vs quests.json
say("\n## Quest entries")
defined = {f"{q}/{e}" for q, qd in quests.items() for e in qd.get("entries", {})}
written = set(W["entry"])
read_entries = set(R["entry"])
for e in sorted(defined - written):
    say(f"NEVER ADDED quest entry {e}: {quests[e.split('/')[0]]['entries'][e.split('/')[1]][:80]!r}")
for e in sorted(written - defined): say(f"UNDEFINED quest entry written {e} in {sorted(W['entry'][e])}")
for e in sorted(read_entries):
    q, k = e.split("/")
    if q == "?":
        if not any(x.endswith("/" + k) for x in written): say(f"READ but never written quest entry */{k}")
    elif e not in written: say(f"READ but never written quest entry {e} in {sorted(R['entry'][e])}")

# items
say("\n## Items")
for k in sorted(set(W["item"]) | set(R["item"])):
    if k not in items: say(f"UNKNOWN item {k} used in {sorted(W['item'][k] | R['item'][k])}")
for k in sorted(set(R["item"]) - set(W["item"])):
    if k in items: say(f"item {k} is checked/taken but never given by story code (may come from shops/loot): {sorted(R['item'][k])}")

def report(kind, label, ignore=lambda k: False):
    say(f"\n## {label}")
    for k in sorted(set(R[kind]) - set(W[kind])):
        if not ignore(k): say(f"READ never WRITTEN {kind} {k!r}  (read in {sorted(R[kind][k])})")
    for k in sorted(set(W[kind]) - set(R[kind])):
        if not ignore(k): say(f"WRITTEN never READ {kind} {k!r}  (written in {sorted(W[kind][k])})")

report("fact", "Facts")
report("know", "Knowledge")
report("hist", "History events")
report("flag", "NPC flags", ignore=lambda k: "once:" in k)

open(r"C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/check_story_out2.txt", "w", encoding="utf8").write("\n".join(out))
print("\n".join(out))
