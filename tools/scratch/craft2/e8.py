from js import load, save
n = load("npcs")
said = n["npcs"]["maeca"].setdefault("said", [])
assert not any(s.get("text", "").startswith("That's his.") for s in said)
said.append({
    "text": "That's his. Wear it where I can't see it.",
    "when": {"hasTag": "greymuzzle_fang"},
    "once": True,
    "effects": [{"rel": {"npc": "maeca", "affection": -10}}],
})
save("npcs", n)
