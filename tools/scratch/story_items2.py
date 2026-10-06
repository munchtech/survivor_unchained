import json
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\items.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
I = d["items"]
# The believer's seed (LINE_NOTES 2.5, 6.3), in his own word for the deep.
g = I["grimtunnels_lamp"]
assert g["lore"].endswith("he will want it back.")
g["lore"] += " Scratched round the rim, small, in lampling letters, over and over: DOWNSTAIRS. DOWNSTAIRS. DOWNSTAIRS."
# The lamps' logic for the player who reads (LINE_NOTES 6.4; bible, oil and ember).
w = I["wardens_lampiron"]
old = "a smith's mark: a ring with a hammer across it."
assert old in w["lore"]
w["lore"] = w["lore"].replace(old, old + " It was made to hold ember, not oil.")
open(P, "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("ok")
