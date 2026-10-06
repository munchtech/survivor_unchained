"""Print rules.json rules whose JSON mentions any of the given words. Usage: rules_s5.py WORD [WORD ...]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a54dc034ed29f2e02\godot\data\content\rules.json"
data = json.load(open(p, encoding="utf-8"))
print("top keys:", list(data.keys()))
for r in data["rules"]:
    s = json.dumps(r, ensure_ascii=False)
    if any(w in s for w in sys.argv[1:]):
        print(s)
        print()
