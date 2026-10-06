"""Print a conversation (or one node) compactly: node ids, variants with their `when`, choices with
show/when/effects/goto. Usage: show_s5.py CONV [NODE ...]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
C = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1\godot\data\content"
d = json.load(open(C + r"\dialogue.json", encoding="utf-8"))
conv = d[sys.argv[1]]
want = set(sys.argv[2:])
def j(x): return json.dumps(x, ensure_ascii=False)
if not want:
    print("entry:", j(conv.get("entry")))
for k, n in conv["nodes"].items():
    if want and k not in want: continue
    print(f"== {k}" + (f"  speaker={n['speaker']}" if n.get("speaker") else "") + (f"  effects={j(n['effects'])}" if n.get("effects") else ""))
    t = n["text"]; vs = t if isinstance(t, list) else [{"text": t}]
    for i, v in enumerate(vs):
        print(f"  [{i}]" + (f" when={j(v['when'])}" if v.get("when") else "") + (f" eff={j(v['effects'])}" if v.get("effects") else ""))
        print("      " + v["text"])
    for c in n.get("choices", []):
        extra = {k2: v2 for k2, v2 in c.items() if k2 not in ("text",)}
        print(f"  > {c.get('text')}  {j(extra)}")
    for k2 in n:
        if k2 not in ("id", "text", "choices", "speaker", "effects"):
            print(f"  ({k2}: {j(n[k2])})")
