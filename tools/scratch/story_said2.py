import json
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\npcs.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
fix = {
    # Jory drove the Company's wagons, not his own cart; Harlan's crack is the patter stopping dead.
    "Sold him the cart at cost. At cost.": "Coyle and Nephew, the new sign was going to say. Coyle and—",
    # Tam is earnest, never loud on the page: the capitals are Snib's.
    "The stream's clear and Pa says I was right and I WAS.": "The stream's clear and Pa says I was right, and I was.",
}
n = 0
for npc in d["npcs"].values():
    for s in npc.get("said") or []:
        if s["text"] in fix:
            s["text"] = fix[s["text"]]; n += 1
assert n == len(fix), n
open(P, "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("ok")
