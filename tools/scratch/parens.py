"""Parentheticals in spoken lines: lowercase ones (delivery directions) and short
capitalised fragments (which may be directions read as narration)."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content"
d = json.load(open(ROOT + r"\dialogue.json", encoding="utf-8"))
seen = {}
for cid, c in d.items():
    for nid, n in c["nodes"].items():
        t = n.get("text")
        for i, v in enumerate(t if isinstance(t, list) else [{"text": t or ""}]):
            for m in re.finditer(r"\(([^()]*)\)", v["text"]):
                p = m.group(1).strip()
                if p.startswith("explicit scene"):
                    continue
                words = len(p.split())
                low = p[:1].islower()
                if low or words <= 6:
                    seen.setdefault(p, []).append(f"{cid}.{nid}.{i}" + (" [narrator node]" if n.get("speaker") == "narrator" else ""))
for p, ids in sorted(seen.items(), key=lambda kv: (not kv[0][:1].islower(), kv[0])):
    print(f"({p})  <- {', '.join(ids[:4])}{' +' + str(len(ids)-4) if len(ids) > 4 else ''}")
