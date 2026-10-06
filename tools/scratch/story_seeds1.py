"""The editorial's cheap Act 1 seeds (handoff step 3), in the data. Each file is
rewritten in its own format: indent 1, ensure_ascii False, CRLF, trailing CRLF."""
import json

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content"


def load(name):
    return json.loads(open(f"{ROOT}\\{name}", "rb").read().decode("utf-8"))


def save(name, d):
    out = json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
    open(f"{ROOT}\\{name}", "wb").write(out.encode("utf-8"))


def text_swap(node, old, new):
    t = node["text"]
    if isinstance(t, list):
        hits = [v for v in t if old in v["text"]]
        assert len(hits) == 1, (old, len(hits))
        hits[0]["text"] = hits[0]["text"].replace(old, new)
    else:
        assert old in t, old
        node["text"] = t.replace(old, new)


def add_choice(node, choice, before_text):
    """Insert a choice before the first one whose text is before_text."""
    ch = node["choices"]
    assert not any(c.get("goto") == choice.get("goto") and c.get("text") == choice["text"] for c in ch), "already there"
    i = next(i for i, c in enumerate(ch) if c["text"] == before_text)
    ch.insert(i, choice)


d = load("dialogue.json")

# --- Maeca keeps Ashford in her mouth (VOICES); her plate stops saying it too,
# so the word is first earned in conversation (Rook, Wenna, Holloway).
text_swap(d["maeca"]["nodes"]["first"],
          "Maeca Barefoot, of the Ashford garrison. What's left of it.",
          "Maeca. Barefoot, before you ask.")

# --- "Gone to the Morrow": the valley's word for dying is the god's name.
wenna = d["wenna"]["nodes"]
text_swap(wenna["fever"],
          "Half the valley coughing green and the other half burying them. Same smell as your bottle, child. Same smell exactly.",
          "Half the valley coughing green and the other half burying them. \"Gone to the Morrow,\" they say up here, like it's a walk. They died, child. Same smell as your bottle. Same smell exactly.")

# Wenna will not burn ember.
wenna["tallow"] = {
    "id": "tallow",
    "text": "I burn fat, child. Fat's honest. Fat was a pig.",
    "choices": [
        {"text": "Something else.", "goto": "hub"},
        {"text": "Goodbye.", "end": True},
    ],
}
add_choice(wenna["hub"], {"text": "Tallow lamps? Everyone else burns ember.", "once": "tallow", "goto": "tallow"}, "What do you sell?")

rook = d["rook"]["nodes"]
rook["valley"] = {
    "id": "valley",
    "text": "Ashford was. Half of it went to the Morrow in one night, pet, and the other half the year after, coughing. Don't ask Holloway about it. Don't ask Maeca. And don't ask me twice.",
    "choices": [
        {"text": "Something else.", "goto": "hub"},
        {"text": "Goodbye, Rook.", "end": True},
    ],
}
add_choice(rook["town"], {"text": "What's up the valley?", "once": "valley", "goto": "valley"}, "Something else.")

# --- Chid's flame was never for seeing by.
text_swap(d["chid"]["nodes"]["shrine"],
          "Kept the dead lying down where you'd put them. Then the Order left",
          "Kept the dead lying down where you'd put them. It was never for seeing by, you know; it was for keeping company. Then the Order left")

# --- The carter wears thin. Chid carries the survivor in himself (bible, Chid);
# the carter is his white lie, and it gets thinner with every death.
chid = d["chid"]["nodes"]
woke = chid["woke"]
first_lit, first = woke["text"]
assert first_lit["when"] == {"fact": "shrine.lit", "eq": True}, first_lit
woke["text"] = [
    {"when": {"fact": "player.deaths", "gte": 4},
     "text": "Up again. Up's good. (He has the kettle on already.) The carter brought you in, before you ask. You'll be sore a day or two. Whatever did it has your things."},
    {"when": {"fact": "player.deaths", "eq": 3},
     "text": "You're up. A carter brought you in. (He isn't looking at you.) Well. Someone did. Someone always does. You'll be sore a day or two, and whatever did this still has your things."},
    {"when": {"fact": "player.deaths", "eq": 2},
     "text": "You're awake! A carter found you. The same carter, as it happens; he's starting to think you're doing it on purpose. (He laughs, and stops.) You'll be sore a day or two. Whatever did this is still out there. It'll have your things."},
    first_lit,
    first,
]
add_choice(woke, {"text": "Which carter, Chid?", "show": {"fact": "player.deaths", "gte": 3}, "once": "carter", "goto": "carter"}, "Where did I fall?")
chid["carter"] = {
    "id": "carter",
    "text": "...You know, I never asked his name. I should ask his name. Next time. (He puts a cup in your hands.) Drink that. It's only hot water. There's nothing in it but hot.",
    "choices": [
        {"text": "Thank you, Chid.", "end": True},
        {"text": "Where did I fall?", "goto": "where"},
    ],
}

save("dialogue.json", d)

# --- The folk. New lines go on the end: a folk line's voice id is its place.
folk = load("folk.json")
L = folk["lines"]
by_text = {x["text"]: x for x in L}
# Funerals said "this morning" for ever after; say what happened, not when.
a = by_text["They buried Aldo this morning. The Captain carried the front of the coffin himself."]
a["text"] = "The Captain carried the front of Aldo's coffin himself. Wouldn't let anyone spell him."
n = by_text["They buried Brannoc's girl behind the shrine this morning. Chid sang. Chid can't sing. Nobody minded."]
n["text"] = "They buried Brannoc's girl behind the shrine. Chid sang. Chid can't sing. Nobody minded."
new = [
    {"text": "Old Oswin's gone to the Morrow. Sat down in his chair after his dinner and went.", "night": False, "when": {"day": {"gte": 3}}},
    {"text": "Lamps are lit. Stay where they reach, or it's the Morrow for you.", "watch": True, "night": True},
    {"text": "No carts on the Old Road since the wolves. So who keeps bringing that one in?", "when": {"fact": "player.deaths", "gte": 2}},
]
for x in new:
    assert x["text"] not in by_text
    L.append(x)
save("folk.json", folk)

# --- The plate, the trait and the ember's lore.
npcs = load("npcs.json")
assert npcs["npcs"]["maeca"]["title"] == "Last of the Ashford Garrison"
npcs["npcs"]["maeca"]["title"] = "Hunter, of the Hollow"
save("npcs.json", npcs)

arch = load("archetypes.json")
t = arch["traits"]["risen_once"]
assert t["text"].startswith("You have died and come back.")
t["text"] = t["text"].replace("You have died and come back.", "You fell, and got up again.")
save("archetypes.json", arch)

items = load("items.json")["items"]
it = load("items.json")
I = it["items"]
assert I["ember_shard"]["description"] == "A stone that kept some of its light. It does not keep forever."
I["ember_shard"]["description"] += " Hold it to your ear in a quiet room, and the room is not quite quiet."
assert I["blasting_ember"]["description"].endswith("Or up.")
I["blasting_ember"]["description"] += " It is warm, and warmer when you are afraid."
assert I["slurry_sample"]["description"] == "Warm, faintly glowing sludge scraped from a pipe."
I["slurry_sample"]["description"] = "Warm, faintly glowing sludge scraped from a pipe. It smells like a chapel lamp, and a little like a wound."
save("items.json", it)
print("ok")
