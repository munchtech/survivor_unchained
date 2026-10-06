"""Print a conversation's node: python dlg.py NPC NODE"""
import json, sys
d = json.load(open(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7debf1459f14dfe7\godot\data\content\dialogue.json", encoding="utf-8"))
npc, node = sys.argv[1], sys.argv[2]
n = d[npc]["nodes"][node]
print("TEXT:", json.dumps(n.get("text"), ensure_ascii=False)[:1200])
for k in n:
    if k not in ("text", "choices", "id"):
        print(k.upper() + ":", json.dumps(n[k], ensure_ascii=False)[:400])
for c in n.get("choices", []):
    rest = {k: v for k, v in c.items() if k != "text"}
    print(" *", c.get("text"), "|", json.dumps(rest, ensure_ascii=False)[:300])
