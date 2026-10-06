"""Print a conversation from dialogue.json readably.

usage: python show.py CONV [NODE...] [--brief]
"""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3047062bf0f80c54\godot\data\content\dialogue.json"
d = json.load(open(ROOT, encoding="utf-8"))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
brief = "--brief" in sys.argv
conv = d[args[0]]
want = set(args[1:])
SKIP_ACT = {"trade", "sellpelts", "craft"}


def cond(w):
    if w is None:
        return ""
    s = json.dumps(w, ensure_ascii=False)
    return s if len(s) < 160 or not brief else s[:157] + "..."


if not want:
    print("ENTRY:")
    for e in conv.get("entry", []):
        print("  ", e.get("node"), "<-", cond(e.get("when")))
for nid, n in conv["nodes"].items():
    if want and nid not in want:
        continue
    print(f"\n== {nid}" + (f"  [speaker {n['speaker']}]" if "speaker" in n else ""))
    t = n.get("text")
    if isinstance(t, str):
        print("   ", t)
    elif isinstance(t, list):
        for i, v in enumerate(t):
            print(f"   #{i} {cond(v.get('when'))}\n        {v.get('text')}")
    if n.get("effects") and not brief:
        print("    effects:", json.dumps(n["effects"], ensure_ascii=False))
    if n.get("next"):
        print("    next ->", n["next"])
    for c in n.get("choices", []):
        if c.get("action") in SKIP_ACT:
            continue
        line = f"    > {c.get('text')}"
        if c.get("goto"):
            line += f"  -> {c['goto']}"
        if c.get("action"):
            line += f"  [action {c['action']}]"
        if c.get("when") and not brief:
            line += f"  when {cond(c.get('when'))}"
        if c.get("once"):
            line += f"  once:{c['once']}"
        print(line)
