"""Chid gives The Keeper's Office (keepers_office): on Act 2's first morning (chid.office), or at his
waking after a lost fight once Act 2 has begun, if he has not given it yet. WRITING_PASS 22.3."""
import sys
from jsonio_s6 import load, save

d = load("dialogue.json")
c = d["chid"]
N = c["nodes"]

ACT2 = {"fact": "chapter.done", "eq": True}
NOT_GIVEN = {"not": {"npcFlag": {"npc": "chid", "key": "gave:office", "eq": True}}}
GIVE = [{"give": "keepers_office"}, {"npcFlag": {"npc": "chid", "key": "gave:office", "value": True}}]
THANKS = {"text": "Thank you, Chid.", "effects": [{"rel": {"npc": "chid", "affection": 10}}], "end": True}

if "office" in N:
    sys.exit("already there")

# He has it ready for her: the shrine is marked until he has given it.
c["marker"].append({"when": {"all": [{"met": "chid"}, ACT2, NOT_GIVEN]}, "mark": "!"})

# After the death wakings and the first meeting, before the callbacks.
i = next(k for k, e in enumerate(c["entry"]) if e["node"] == "first")
c["entry"].insert(i + 1, {"when": {"all": [{"met": "chid"}, ACT2, NOT_GIVEN]}, "node": "office"})

ASK_END = {"text": "What's at the end?", "once": "office_end", "goto": "office_end"}
ASK_WHO = {"text": "Who wrote it?", "once": "office_who", "goto": "office_who"}

N["office"] = {
    "id": "office",
    "text": "You've been up the Tower. (He doesn't ask what she told you.) Here. (He has a small book in both hands, held the way you hold a bird.) I want you to have this. It's only an old office: the watch-hours, what the keepers said at night. Nobody's said them in a long while. (He opens it at the last page, and doesn't look at it.) There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in the dark.",
    "effects": GIVE,
    "choices": [ASK_END, ASK_WHO, THANKS],
}
N["office_end"] = {
    "id": "office_end",
    "text": "(He puts his hand flat on the cover.) Not now, I said! ...It's the end of the watch. One keeper asks, and the other one answers, so nobody has to sit up the whole night on their own. That's what an office is, really. Somebody answering.",
    "choices": [ASK_WHO, THANKS],
}
N["office_who"] = {
    "id": "office_who",
    "text": "Oh, a keeper. One of the old ones. Lovely hand, hasn't he? Nobody makes a C like that any more.",
    "choices": [ASK_END, THANKS],
}

# At the waking after a lost fight in Act 2, with the book not yet given: he has it in his hands,
# and gives it as she goes (either way out of the waking). First, so it wins over the places' pointers.
cc = N["carried_chid"]
cc["text"].insert(0, {
    "when": {"all": [ACT2, NOT_GIVEN]},
    "text": "You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and that's all it's cost you: a night. They come round again; it's the one thing you can say for them. (He doesn't look at you.) Somebody brought you in. A carter, I expect. (He has a small book in both hands, held the way you hold a bird.) I was keeping this for you. It's only an old office, what the keepers said at night. There's a bit at the end. ...Read it before you go out again. Please.",
})
gift = {"if": {"all": [ACT2, NOT_GIVEN]}, "then": GIVE}
for ch in cc["choices"]:
    ch.setdefault("effects", []).append(gift)
    # keep key order readable: text, once, effects, goto/end
    order = ["text", "once", "show", "when", "effects", "goto", "end"]
    items = sorted(ch.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)
    ch.clear(); ch.update(items)

save("dialogue.json", d)
print("done")
