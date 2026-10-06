"""Phase 2's conversations: Brannoc's fang, Wenna's still-room and bench, Maeca's braid.
The words are the story lead's (October 2026), verbatim."""
from js import load, save

d = load("dialogue")
STREAM = {"any": [{"fact": "stream.clear", "eq": True}, {"fact": "beasts.outcome", "eq": "cured"}]}


def insert_after(choices, after_text, new):
    i = next(k for k, c in enumerate(choices) if c.get("text") == after_text)
    choices[i + 1:i + 1] = new


# Brannoc: the fang, offered while it is held; it opens his forge, where it is set.
b = d["brannoc"]
insert_after(b["nodes"]["hub"]["choices"], "Will you work my gear?", [
    {"text": "Greymuzzle's fang. Will you set it?", "when": {"hasItem": "greymuzzle_fang"}, "show": {"hasItem": "greymuzzle_fang"}, "goto": "fang"},
])
b["nodes"]["fang"] = {
    "id": "fang",
    "text": "(He holds it up to the forge-light and turns it.) Worn flat on the one side. He chewed on that side.",
    "choices": [
        {"text": "Will you work my gear?", "action": "craft"},
        {"text": "Something else.", "goto": "hub"},
        {"text": "Goodbye.", "end": True},
    ],
}
# A commission ready on his anvil shows over his head.
b["marker"].append({"when": {"fact": "commission.done", "eq": True}, "mark": "!"})

# Wenna: brewing from the start; her bench once the stream is clean.
w = d["wenna"]
i = next(k for k, c in enumerate(w["nodes"]["hub"]["choices"]) if c.get("text") == "What do you sell?")
w["nodes"]["hub"]["choices"][i:i] = [
    {"text": "Brew me something.", "action": "still"},
    {"text": "Will you stitch something into my gear?", "when": STREAM, "locked": "Not until the stream runs clean", "action": "craft"},
]

# Maeca: with the Pack allied, she offers to braid what they shed; it is ready the next day.
m = d["maeca"]
first = next(k for k, e in enumerate(m["entry"]) if e.get("node") == "first")
m["entry"][first + 1:first + 1] = [
    {"when": {"all": [{"met": "maeca"}, {"fact": "shedfur.ready", "eq": True}, {"not": {"fact": "shedfur.given", "eq": True}}]}, "node": "shed_fur_braid"},
    {"when": {"all": [{"met": "maeca"}, {"fact": "pack.allied", "eq": True}, {"not": {"fact": "shedfur.offered", "eq": True}}]}, "node": "shed_fur_offer"},
]
after = [{"text": "Something else.", "goto": "hub"}, {"text": "Goodbye.", "end": True}]
m["nodes"]["shed_fur_offer"] = {
    "id": "shed_fur_offer",
    "text": "They've been leaving fur on the thorn by the Blind. For you, I think. Give me an evening.",
    "effects": [{"set": {"shedfur.offered": True}}, {"later": {"days": 1, "id": "shedfur.ready", "effect": [{"set": {"shedfur.ready": True}}]}}],
    "choices": after,
}
m["nodes"]["shed_fur_braid"] = {
    "id": "shed_fur_braid",
    "text": "(She sits with her back to the fire and braids it on her knee, grey and grey and white, the way you'd braid a child's hair. She doesn't talk. When it's done she bites the end off.) Next to the skin. They'll know you in the dark.",
    "effects": [{"give": "shed_fur_braid", "made": "maeca:shedFur"}, {"set": {"shedfur.given": True}}],
    "choices": after,
}
save("dialogue", d)

# Maeca's once-only bark when she first sees the fang worn: her regard falls (story lead: -10 affection).
n = load("npcs")
n["maeca"].setdefault("said", []).append({
    "text": "That's his. Wear it where I can't see it.",
    "when": {"hasTag": "greymuzzle_fang"},
    "once": True,
    "effects": [{"rel": {"npc": "maeca", "affection": -10}}],
})
save("npcs", n)
