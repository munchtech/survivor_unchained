"""Print the loot lead's Legendaries and set pieces from their worktree's items.json (read-only)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a9a9c345a35e1fcad\godot\data\content\items.json"
d = json.load(open(P, encoding="utf-8"))
items = d["items"] if "items" in d else d
for k, v in items.items():
    if not isinstance(v, dict):
        continue
    s = json.dumps(v, ensure_ascii=False)
    if v.get("rarity", 0) >= 4 or v.get("set") or "legendary" in s.lower() or '"sets"' in s:
        print("==", k, "|", v.get("name"), "| rarity", v.get("rarity"), "| kind", v.get("kind"), "| set", v.get("set"))
        for f, val in v.items():
            if f in ("id", "name", "rarity", "kind", "set", "icon", "value", "stack", "stats", "mods", "weapon", "armor", "slot"):
                continue
            print("   ", f, ":", json.dumps(val, ensure_ascii=False)[:700])
for key in ("sets", "legendaries"):
    if key in d:
        print("###", key)
        print(json.dumps(d[key], ensure_ascii=False, indent=1)[:4000])
