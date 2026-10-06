"""The town notices (editorial I-15, LINE_NOTES 10): each named person's barks
that stop being true move to "said" with the condition that keeps them true,
and each gains a line for what the survivor settled. Every line is twelve
words or fewer."""
import json

P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\npcs.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
N = d["npcs"]

UNSETTLED_BEASTS = {"not": {"fact": "beasts.outcome", "exists": True}}
CARAVAN_OPEN = {"not": {"fact": "caravan.survivors", "exists": True}}
NOT_RESCUED = {"not": {"fact": "caravan.survivors", "eq": "rescued"}}
STREAM_FOUL = {"not": {"fact": "stream.clear", "eq": True}}


def eq(f, v):
    return {"fact": f, "eq": v}


def move(npc, key, text, when, night):
    lst = N[npc][key]
    assert text in lst, (npc, key, text)
    lst.remove(text)
    add(npc, text, when, night, new=False)


def add(npc, text, when=None, night=None, new=True):
    assert not new or len(text.replace("...", "").split()) <= 12, text
    line = {"text": text}
    if night is not None:
        line["night"] = night
    if when is not None:
        line["when"] = when
    said = N[npc].setdefault("said", [])
    assert all(s["text"] != text for s in said), text
    said.append(line)


# Holloway
move("holloway", "barks", "Five a pelt. Fifty for the old grey one.", UNSETTLED_BEASTS, False)
add("holloway", "Pelt book's closed. I'll not miss writing in it.",
    {"all": [{"fact": "beasts.outcome", "exists": True}, {"not": eq("beasts.outcome", "ignored")}]}, False)
add("holloway", "Corran's in the ground. That's one debt paid.", eq("corran.home", True), False)
add("holloway", "One caravan home. One. I'll take it.", eq("caravan.survivors", "rescued"), False)

# Maeca
move("maeca", "barks", "They're not hunting. They're running.", UNSETTLED_BEASTS, False)
move("maeca", "barks", "Something's got the whole wood on edge.", UNSETTLED_BEASTS, False)
move("maeca", "nightBarks", "The Pack's loud tonight.", {"not": eq("beasts.outcome", "slaughtered")}, True)
move("maeca", "nightBarks", "Somewhere out there an old wolf's coughing. Listen.", UNSETTLED_BEASTS, True)
add("maeca", "Hear that? They're hunting again. Deer.", eq("beasts.outcome", "cured"), True)
add("maeca", "The Pack's lying up by the east wall. Leave them be.", eq("beasts.outcome", "allied"), True)
add("maeca", "Nothing calls in the Hollow now. Nothing.", eq("beasts.outcome", "slaughtered"), False)

# Chid
move("chid", "barks", "It used to work, you know. The shrine.", {"not": eq("shrine.lit", True)}, False)
add("chid", "It works! It works. I keep checking.", eq("shrine.lit", True), False)
add("chid", "Up and about! Up's very good.", {"fact": "player.deaths", "gte": 1}, False)
add("chid", "Two candles in for her. One's for Brannoc; don't tell him.", eq("nell.buried", True), True)

# Harlan: everything he said was about a boy not yet home.
move("harlan", "barks", "Late. Jory's never late.", CARAVAN_OPEN, False)
move("harlan", "barks", "Salt, iron, cloth. Whatever you need, when the wagons come.", CARAVAN_OPEN, False)
move("harlan", "barks", "Somebody knows something.", CARAVAN_OPEN, False)
N["harlan"]["barks"].append("Salt and iron, friend. Cloth, when I can get it.")
move("harlan", "nightBarks", "Every wagon on that road's his, in the dark.", NOT_RESCUED, True)
move("harlan", "nightBarks", "Can't sleep. Won't.", CARAVAN_OPEN, True)
move("harlan", "nightBarks", "Jory hated the dark. Hated it. Slept with a candle till he was fourteen.", NOT_RESCUED, True)
add("harlan", "Jory's asleep in Rook's good room. I keep going to look.", eq("caravan.survivors", "rescued"), False)
add("harlan", "He sleeps with the lamp lit. So do I, now.", eq("caravan.survivors", "rescued"), True)
add("harlan", "Sold him the cart at cost. At cost.", eq("caravan.survivors", "dead"), False)
add("harlan", "Mister Coyle, he calls me. In my own shop.", eq("jory.knows_be", True), False)

# Wenna
move("wenna", "barks", "The animals were never like this. Never.", STREAM_FOUL, False)
move("wenna", "barks", "The water tastes wrong this year.", STREAM_FOUL, False)
add("wenna", "Water's sweet. Sweet! I'd forgotten.",
    {"all": [eq("stream.clear", True), {"any": [eq("beasts.outcome", "cured"), eq("beasts.outcome", "allied")]}]}, False)
add("wenna", "Clean water, and nothing left in the wood to drink it.",
    {"all": [eq("stream.clear", True), eq("beasts.outcome", "slaughtered")]}, False)

# Tam: right, every time.
move("tam", "barks", "They drank from the stream and fell down.", UNSETTLED_BEASTS, None)
move("tam", "barks", "I told the Watch. The Watch laughed.", UNSETTLED_BEASTS, None)
add("tam", "The stream's clear and Pa says I was right and I WAS.", eq("beasts.outcome", "cured"))
add("tam", "Somebody killed all the wolves. Even the ones that were only sick.", eq("beasts.outcome", "slaughtered"))
add("tam", "Ground knocks under our barn. Pa says pipes. We've got no pipes.", eq("tremor.felt", True))

# Brannoc
add("brannoc", "Low Kiln's three days. She'll be there by now.", eq("nell.told", "lie"), False)
add("brannoc", "Twelve, I made. Twelve.", {"any": [eq("nell.told", "gone"), eq("nell.told", "risen")]}, False)
add("brannoc", "Forge is lit. Don't come in.", eq("nell.buried", True), True)

# Rook
add("rook", "Harlan's not eating. I've sent bread. He's sent it back.", eq("caravan.survivors", "dead"), False)
add("rook", "Hook's empty. I know. Leave it.", eq("nell.buried", True), False)

# Keegan, Rav
add("keegan", "Chapter four. Chapter four. ...Good morning.", eq("keegan.saw_risen", True), False)
add("rav", "Oh, Mam.", eq("redcowl", "dead"), True)

out = json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
open(P, "wb").write(out.encode("utf-8"))
print("ok")
