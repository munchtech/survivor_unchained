#!/usr/bin/env python3
"""Check the romance data drafts the way godot/tests/StoryLint.cs reads the
story, without needing .NET: swap each draft conversation into
dialogue.json (in memory), then check reachability, the explicit slots,
facts read but never written, and that every condition and change uses a
key the game understands.

    python3 docs/romance/data/check.py

Nothing in the game is changed. Facts written by the zone scripts are found
by searching the C# for the key, as StoryLint does."""
import json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CONTENT = os.path.join(ROOT, "godot", "data", "content")
FILES = ["dialogue.json", "quests.json", "rules.json", "concerns.json", "folk.json", "shops.json", "npcs.json", "archetypes.json"]

COND_KEYS = {"fact", "knows", "notKnows", "bg", "archetype", "hasItem", "hasTag", "trait", "met", "history", "sex", "qty",
             "rel", "npcFlag", "npcKnows", "faction", "quest", "day", "level", "gold", "kills", "time", "zone", "all", "any", "not",
             "eq", "ne", "gte", "lte", "gt", "lt", "exists"}
CHANGE_KEYS = {"set", "add", "learn", "text", "rel", "quiet", "npcFlag", "faction", "give", "take", "qty", "rarity", "gold", "quest",
               "history", "witnesses", "tell", "trait", "condition", "cure", "zone", "later", "xp", "notice", "tone", "if", "then", "else"}
CONDITIONS = {"wounded", "blightsick", "poisoned", "blessed", "rested", "wolfscent", "hunted", "warmed"}

dialogue = json.load(open(os.path.join(CONTENT, "dialogue.json")))
drafts = {}
for f in sorted(glob.glob(os.path.join(HERE, "*.json"))):
    for cid, conv in json.load(open(f)).items():
        drafts[cid] = conv
        dialogue[cid] = conv
others = [json.load(open(os.path.join(CONTENT, f))) for f in FILES if f != "dialogue.json"]
code = "\n".join(open(p, encoding="utf-8").read() for d in ("logic", "src")
                 for p in glob.glob(os.path.join(ROOT, "godot", d, "**", "*.cs"), recursive=True))

problems = []
read, written = set(), set()

def walk(e, cond, where):
    if isinstance(e, dict):
        for k, v in e.items():
            # (A node may be called "show"; a node has words, a question has none.)
            if k in ("when", "show", "if") and not (isinstance(v, dict) and "text" in v):
                if where in drafts: check_cond(v, where)
                walk(v, True, where)
            elif cond and k == "fact" and isinstance(v, str):
                read.add(v)
            elif not cond and k in ("set", "add") and isinstance(v, dict):
                written.update(v.keys())
            else:
                walk(v, cond, where)
    elif isinstance(e, list):
        for x in e: walk(x, cond, where)

def check_cond(c, where):
    if isinstance(c, dict):
        for k, v in c.items():
            if k not in COND_KEYS: problems.append(f"{where}: unknown condition key '{k}'")
            if k in ("all", "any"): [check_cond(x, where) for x in v]
            if k == "not": check_cond(v, where)

def check_changes(lst, where):
    for ch in lst or []:
        for k, v in ch.items():
            if k not in CHANGE_KEYS: problems.append(f"{where}: unknown change key '{k}'")
            if k == "condition" and v.get("id") not in CONDITIONS: problems.append(f"{where}: unknown condition id {v.get('id')}")
            if k in ("then", "else"): check_changes(v if isinstance(v, list) else [v], where)
            if k == "later": check_changes(v["effect"] if isinstance(v["effect"], list) else [v["effect"]], where)

for cid, conv in dialogue.items():
    walk(conv, False, cid)
for o in others:
    walk(o, False, "content")

for cid, conv in drafts.items():
    nodes = conv["nodes"]
    if conv["entry"][-1].get("when"): problems.append(f"{cid}: last entry has a condition")
    reach, stack = set(), [e["node"] for e in conv["entry"]]
    while stack:
        n = stack.pop()
        if n not in nodes: problems.append(f"{cid}: points at missing node {n}"); continue
        if n in reach: continue
        reach.add(n)
        node = nodes[n]
        if node.get("id") != n: problems.append(f"{cid}.{n}: id is {node.get('id')}")
        check_changes(node.get("effects"), f"{cid}.{n}")
        if not node.get("choices") and not node.get("next"): problems.append(f"{cid}.{n}: no choices and no next")
        if node.get("next"): stack.append(node["next"])
        for c in node.get("choices") or []:
            check_changes(c.get("effects"), f"{cid}.{n}")
            if c.get("goto"): stack.append(c["goto"])
            if not (c.get("goto") or c.get("end") or c.get("action")): problems.append(f"{cid}.{n}: a choice that goes nowhere")
            if c.get("goto") == n and not (c.get("effects") or c.get("action") or c.get("once")):
                problems.append(f"{cid}.{n}: choice returns to its own node")
        texts = node["text"] if isinstance(node["text"], list) else [{"text": node["text"]}]
        slots = [t for t in texts if t["text"].startswith("[explicit scene:")]
        for t in slots:
            w = t.get("when") or {}
            if w.get("fact") != "settings.intimacy" or w.get("eq") != "full": problems.append(f"{cid}.{n}: slot not behind settings.intimacy = full")
        if slots and not any(not t.get("when") and not t["text"].startswith("[explicit scene:") for t in texts):
            problems.append(f"{cid}.{n}: slot with no cut-away")
        if isinstance(node["text"], list) and node["text"][-1].get("when"):
            problems.append(f"{cid}.{n}: last text variant has a condition (fine for the game, but no fallback line)")
    for n in nodes:
        if n not in reach: problems.append(f"{cid}.{n}: nothing leads here")

never = sorted(f for f in read if f not in written and not f.startswith("settings.") and f'"{f}"' not in code)
for f in never: problems.append(f"read, never written: {f}")

print(f"{len(drafts)} draft conversations: {', '.join(drafts)}")
print(f"{len(read)} facts read, {len(written)} written in the content")
if problems:
    print("\n".join(problems)); sys.exit(1)
print("clean")
