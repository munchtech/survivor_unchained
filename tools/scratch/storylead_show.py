"""Story lead's node viewer (own name: the scratchpad is shared).
storylead_show.py conv [node ...]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content"
d = json.load(open(f"{ROOT}\\dialogue.json", encoding="utf-8"))
c = d[sys.argv[1]]
nodes = sys.argv[2:] or list(c["nodes"].keys())
if len(sys.argv) == 2:
    print("ENTRY", json.dumps(c.get("entry"), ensure_ascii=False))
for nid in nodes:
    n = c["nodes"][nid]
    print(f"== {nid} speaker={n.get('speaker')}" + (f" eff={json.dumps(n['effects'], ensure_ascii=False)[:300]}" if n.get("effects") else ""))
    t = n.get("text")
    for v in (t if isinstance(t, list) else [{"text": t}]):
        print("  ", json.dumps(v.get("when"), ensure_ascii=False) if v.get("when") else "", v["text"])
    for ch in n.get("choices") or []:
        extra = {k: ch[k] for k in ("show", "when", "effects", "action", "once", "end") if k in ch}
        print("   >", ch.get("text"), "->", ch.get("goto"), json.dumps(extra, ensure_ascii=False)[:400] if extra else "")
    if n.get("next"): print("   next", n["next"])
