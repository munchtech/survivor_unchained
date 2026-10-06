"""Clip facts from animation's manifest: length, fps, layer, for the clips named."""
import json, os, sys
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aece7b87e89b13f19"
m = json.load(open(os.path.join(G, "tools", "anim", "manifest.json"), encoding="utf-8"))
items = m if isinstance(m, list) else m.get("clips", list(m.values()))
want = set(sys.argv[1:])
for it in items:
    if isinstance(it, dict) and (not want or it.get("clip") in want):
        print({k: v for k, v in it.items() if k not in ("note", "changes")})
