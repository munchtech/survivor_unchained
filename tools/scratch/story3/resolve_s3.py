"""Resolve the one dialogue.json conflict by keeping both sides: the integration branch's new
Maeca nodes (shed fur), then story's (fire). Both were added at the end of Maeca's nodes and
share the closing lines of a node after the conflict."""
import json, sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot\data\content\dialogue.json"
t = open(p, "rb").read().decode("utf-8")
a = t.index("<<<<<<< HEAD\r\n")
b = t.index("=======\r\n", a)
c = t.index(">>>>>>> origin/claude/vigilant-galileo-l6jqyx\r\n", b)
before, head, theirs = t[:a], t[a + len("<<<<<<< HEAD\r\n"):b], t[b + len("=======\r\n"):c]
after = t[c + len(">>>>>>> origin/claude/vigilant-galileo-l6jqyx\r\n"):]
close = "\r\n   }\r\n"
k = after.index(close) + len(close)
tail, rest = after[:k], after[k:]
merged = before + theirs + tail[:-2] + ",\r\n" + head + tail + rest
if "<<<<<<<" in merged or ">>>>>>>" in merged:
    sys.exit("markers left")
d = json.loads(merged)
dump = json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
if dump != merged:
    print("note: written in the round-trip form")
open(p, "wb").write(dump.encode("utf-8"))
m = d["maeca"]["nodes"]
print([k for k in m if k in ("fire", "shed_fur_offer", "shed_fur_braid")])
print([x["text"] if isinstance(x["text"], str) else "..." for x in m["hub"]["choices"]][-5:])
