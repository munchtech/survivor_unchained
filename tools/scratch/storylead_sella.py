"""Sella's two night barks both opened "Rook's walls are thin"; one finds her bath."""
import json
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\npcs.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
nb = d["npcs"]["sella"]["nightBarks"]
i = nb.index("Rook's walls are thin. Just so you know.")
nb[i] = "I've a bath going cold upstairs. Shame to waste it."
open(P, "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("ok", i)
