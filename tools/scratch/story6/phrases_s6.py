"""Who says each signature phrase: every speaker of each, across dialogue, barks and folk lines."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
C = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7ba8903f4c8261b1\godot\data\content"
d = json.load(open(C + r"\dialogue.json", encoding="utf-8"))
n = json.load(open(C + r"\npcs.json", encoding="utf-8"))
f = json.load(open(C + r"\folk.json", encoding="utf-8"))
lines = []
for c, conv in d.items():
    for k, node in conv.get("nodes", {}).items():
        t = node["text"]; vs = t if isinstance(t, list) else [{"text": t}]
        for x in vs: lines.append((node.get("speaker") or conv.get("npc") or c, f"{c}.{k}", x["text"]))
for grp in ("npcs", "outsiders"):
    for k, p in n[grp].items():
        for b in (p.get("barks") or []) + (p.get("nightBarks") or []) + [s["text"] for s in p.get("said") or []]: lines.append((k, "bark", b))
for l in f["lines"]: lines.append(("folk", "folk", l["text"]))
phrases = ["before you ask", "someone always", "not there", "payment, always", "gone to the morrow", "lie down", "is it morning",
           "lamps are lit", "a light going out", "the arrangement", "i am arranging", "pal", "love", "pet", "child", "friend", "lass", "lad"]
for p in phrases:
    rx = re.compile(r"\b" + re.escape(p) + r"\b", re.I)
    who = {}
    for sp, where, t in lines:
        # the narrator's parenthesised text is not the speaker's words
        spoken = re.sub(r"\([A-Z][^)]*\)", "", t)
        if rx.search(spoken): who.setdefault(sp, []).append(where)
    print(f"{p!r}: " + "; ".join(f"{k} ({len(v)})" for k, v in sorted(who.items(), key=lambda kv: -len(kv[1]))))
    if len(sys.argv) > 1 and p in sys.argv[1:]:
        for sp, where, t in lines:
            m = rx.search(re.sub(r"\([A-Z][^)]*\)", "", t))
            if m: print("    ", sp, where, "|", t[:220])
