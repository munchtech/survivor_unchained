"""Rook says Harlan's "tried to pay me for it twice" in her callback for the
freed teamsters; her gossip for the same news found its own detail."""
import json
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\dialogue.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
v = [x for x in d["rook"]["nodes"]["rumours"]["text"] if x["text"].startswith("Jory Coyle's home and sleeping in my good room")]
assert len(v) == 1
old = "Jory Coyle's home and sleeping in my good room with the lamp lit, and Harlan's tried to pay me for it twice."
assert v[0]["text"].startswith(old)
v[0]["text"] = v[0]["text"].replace(old, "Jory Coyle's home, asleep in my good room with the lamp lit, and Harlan's been up my stairs four times to look at him.")
open(P, "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("ok")
