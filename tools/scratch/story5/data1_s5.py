"""Story data for the owner's 4 October decisions: Redcowl spared (C11's spared ending, Rav's
callback, the town's words), and a lost story fight waking her in town (Chid's waking per fight,
the morning reports, the town's talk). Round-trip safe; refuses to run twice."""
import sys
sys.path.insert(0, r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\story5")
from jsonio_s5 import load, save

def lass_lad(when, female, male):
    """Two variants, the woman's first (Redcowl says lass or lad)."""
    f = {"sex": "female"}
    return [{"when": {"all": [when, f]} if when else f, "text": female}, {"when": when, "text": male} if when else {"text": male}]

def npcflag(npc, key): return {"npcFlag": {"npc": npc, "key": key, "eq": True}}

d = load("dialogue.json")

# ---------------------------------------------------------------- C11, spared
c11 = d["cin_raid_on_the_roost"]
if "spared" in c11["nodes"]: sys.exit("already applied")
c11["entry"] = [{"when": {"fact": "redcowl", "eq": "spared"}, "node": "spared"}, {"node": "bairns"}]
said = {"fact": "redcowl.ashford_said", "eq": True}
square = "Ha! (a laugh, and it costs him) ...You said a word in my camp once, and I let you. Now you've let me. That's us square, {x}. ...Near enough."
owes = "Ha! (a laugh, and it costs him) ...You minded where you swung. That's two I owe, then, {x}. The saw-bones a leg, and you the rest of me."
c11["nodes"]["spared"] = {
    "id": "spared", "speaker": "redcowl",
    "text": [
        {"when": {"all": [said, {"sex": "female"}]}, "text": square.format(x="lass")},
        {"when": said, "text": square.format(x="lad")},
        {"when": {"sex": "female"}, "text": owes.format(x="lass")},
        {"text": owes.format(x="lad")},
    ],
    "next": "flit",
}
c11["nodes"]["flit"] = {
    "id": "flit", "speaker": "redcowl",
    "text": "(cold, to her) We'll be off your road by light. (to the camp, the big voice back) Up, my lot! Boots on! We're flitting!",
    "choices": [{"text": "(Continue.)", "end": True}],
}

# ---------------------------------------------------------------- Rav, told he lives
rav = d["rav"]
at = next(i for i, e in enumerate(rav["entry"]) if e["node"] == "came_back") + 1
rav["entry"].insert(at, {"when": {"all": [{"history": "spared_redcowl"}, {"met": "rav"}, {"not": npcflag("rav", "cb:spared_redcowl")}]}, "node": "cb_spared_redcowl"})
rav["nodes"]["cb_spared_redcowl"] = {
    "id": "cb_spared_redcowl",
    "text": "(Two cups are out before you reach his table, and he fills them both.) Busy night up the ruts, I hear. Heard a man got up off his knee after, on a leg he'd no business still having. (He pushes one across.) Good work, that leg. Whoever did it. ...That one doesn't go on the slate, pal.",
    "effects": [{"npcFlag": {"npc": "rav", "key": "cb:spared_redcowl", "value": True}}],
    "choices": [
        {"text": "He said that's two he owes now. You a leg, and me the rest of him.", "show": {"not": said}, "goto": "owes_two"},
        {"text": "Thanks, Rav.", "goto": "hub"},
    ],
}
rav["nodes"]["owes_two"] = {
    "id": "owes_two",
    "text": "(a breath out through his nose) Did he. ...He's a terrible payer. Always was. (He drinks.) Drink your drink, pal.",
    "choices": [{"text": "Something else.", "goto": "hub"}, {"text": "Goodbye.", "end": True}],
}

# ---------------------------------------------------------------- Chid: carried home from a lost story fight
chid = d["chid"]
chid["entry"].insert(0, {"when": {"all": [{"fact": "player.just_died", "eq": True}, {"fact": "player.carried_home", "exists": True}]}, "node": "carried"})
def people(p): return {"fact": "arena.last.people", "eq": p}
wake = "You wake on the bench in Chid's shrine, and it is morning."
chid["nodes"]["carried"] = {
    "id": "carried", "speaker": "narrator",
    "text": [
        {"when": people("pack"), "text": wake + " Your collar is stiff with a wolf's spit, dried. Nothing ate you. Something carried you out of the Hollow, and somebody else carried you home."},
        {"when": people("kerchiefs"), "text": wake + " Your hands are crossed on your chest, the way the Kerchiefs lay out their dead. You do not remember crossing them."},
        {"when": people("lamplings"), "text": wake + " There is lamp-soot all over your coat in small handprints, where a great many little hands lifted you, and then put you down."},
        {"when": people("dead"), "text": wake + " Over your breastbone, faint as an old bruise, is the print of a mailed hand."},
        {"text": wake},
    ],
    # Cleared before the words are picked; they read the night itself (arena.last), which stays.
    "effects": [{"set": {"player.just_died": False, "player.carried_home": None}}],
    "next": "carried_chid",
}
up = "You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and that's all it's cost you: a night. They come round again; it's the one thing you can say for them. (He doesn't look at you.) "
chid["nodes"]["carried_chid"] = {
    "id": "carried_chid",
    "text": [
        {"when": {"all": [people("pack"), {"not": {"fact": "bane.fires", "eq": True}}]},
         "text": up + "Somebody brought you in off the Hollow road. A carter, I expect. ...Maeca was at the door at first light, asking after you. She wouldn't come in. If anybody knows those wolves, it's Maeca."},
        {"when": people("pack"), "text": up + "Somebody brought you in off the Hollow road. A carter, I expect. They get everywhere, carters."},
        {"when": {"all": [people("kerchiefs"), {"not": npcflag("rav", "once:redcowl")}]},
         "text": up + "Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it was light. He sat with you a while and didn't say much, which isn't like him. He knows that camp, you know. He's stitched up half of it."},
        {"when": people("kerchiefs"), "text": up + "Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it was light. He sat with you a while and didn't say much, which isn't like him."},
        {"when": {"all": [people("lamplings"), {"hasItem": "grimtunnels_lamp"}]},
         "text": up + "Somebody brought you down off the Dig's hill. A carter, I expect. ...That old lamp of yours was lit when you came in. I didn't light it. Those little fellows must have been very taken with it."},
        {"when": people("lamplings"), "text": up + "Somebody brought you down off the Dig's hill. A carter, I expect. I've put the kettle on."},
        {"when": {"all": [people("dead"), {"not": {"fact": "bane.pole", "eq": True}}]},
         "text": up + "Somebody brought you in from the old door. A carter, I expect. (He's quiet a moment, which isn't like him.) I've read about the ones behind that door. In a very old book. Ask me, when you've eaten."},
        {"when": people("dead"), "text": up + "Somebody brought you in from the old door. A carter, I expect. (He's quiet a moment, which isn't like him.) They followed the pole, you know. Always the pole."},
        {"text": up + "Somebody brought you in. A carter, I expect."},
    ],
    "choices": [
        {"text": "Thank you, Chid.", "effects": [{"rel": {"npc": "chid", "affection": 10}}], "end": True},
        {"text": "Who brought me in?", "once": "carried_who", "goto": "carried_who"},
    ],
}
chid["nodes"]["carried_who"] = {
    "id": "carried_who",
    "text": "Oh, somebody kind. There are more of them about at night than you'd think. (He busies himself with the kettle.) ...Eat something. The day's yours.",
    "choices": [{"text": "Thank you, Chid.", "effects": [{"rel": {"npc": "chid", "affection": 10}}], "end": True}],
}
save("dialogue.json", d)

# ---------------------------------------------------------------- the journal
q = load("quests.json")
ents = q["caravan"]["entries"]
items = list(ents.items())
i = [k for k, _ in items].index("roost_raided") + 1
items.insert(i, ("roost_spared", "You took Redcowl's Roost by night, and let him get up off his knee. He is taking his people off the Old Road before first light, and leaving the Coyle wagons where they stand."))
q["caravan"]["entries"] = dict(items)
save("quests.json", q)

# ---------------------------------------------------------------- the mornings after
r = load("rules.json")
rules = r["rules"]
def entry(quest, e): return {"quest": {"id": quest, "entry": e}}
new = [
    {"id": "roost.flitted", "once": True, "when": {"history": "spared_redcowl"}, "effect": [],
     "report": "Before first light the wall saw torches come up out of the ravine and go north over the ridge, where no road goes. Holloway counted them all the way, down to a big man at the back who would not get on a cart, and sent nobody after. Rav watched from the Flagon's door until the last one was over."},
    {"id": "hollow.sang", "once": True, "when": entry("beasts", "hollow_lost"), "effect": [],
     "report": "The Pack sang in the Hollow half the night, the way they do over a kill. Then they stopped, all at once, in the middle of it."},
    {"id": "roost.sang", "once": True, "when": entry("caravan", "roost_repelled"), "effect": [],
     "report": "There was singing up the ravine last night, the slow kind the Kerchiefs keep for burying. Toward dawn it turned to shouting, and then to nothing."},
    {"id": "dig.lamps", "once": True, "when": entry("beasts", "dig_held"), "effect": [],
     "report": "Before dawn a line of little lamps came a long way down the hill from the Dig, toward the wall. It stopped where the wall's lamps reach, and went back up."},
    {"id": "vault.shut", "once": True, "when": entry("vault", "shut"), "effect": [],
     "report": "Out in the Verge the violet went out an hour before dawn, all at once, like a door shutting. Old Oswin says he heard marching first, a long way off, going down."},
]
ids = [x["id"] for x in rules]
for x in new:
    if x["id"] in ids: sys.exit(x["id"] + " already there")
at = ids.index("vault.watched") + 1
r["rules"] = rules[:at] + new + rules[at:]
save("rules.json", r)

# ---------------------------------------------------------------- the town's talk (appended: the index is the voice id)
n = load("npcs.json")
lost = [{"fact": "arena.last.ago", "eq": 1}, {"fact": "arena.last.story", "eq": True}, {"fact": "arena.last.won", "eq": False}]
def add(npc, text, when):
    n["npcs"][npc].setdefault("said", []).append({"text": text, "night": False, "when": when})
add("holloway", "Count was one short last night. It's right this morning. Don't make me write it twice.", {"all": lost})
add("maeca", "Heard you go down in the Hollow. Heard them walk away after. They don't leave meat.", {"all": lost + [{"fact": "arena.last.people", "eq": "pack"}]})
add("rav", "Heard the lads laid you out proper. Hands crossed and all. That's manners, from them.", {"all": lost + [{"fact": "arena.last.people", "eq": "kerchiefs"}]})
add("keegan", "They say the dead carried you back out of the old door. The dead do not, as a rule, give anything back. ...I am making a note.", {"all": lost + [{"fact": "arena.last.people", "eq": "dead"}]})
spared = {"fact": "redcowl", "eq": "spared"}
add("holloway", "Had Redcowl on his knee and let him up. Road's quiet. I'll give you that.", spared)
add("rav", "Quiet up the ruts, these nights. I don't miss the trade.", spared)
add("maeca", "Heard you let the red one walk. ...Good.", spared)
save("npcs.json", n)

# ---------------------------------------------------------------- what's on their minds, and the square's talk
c = load("concerns.json")
c["redcowl"] = [
    {"when": {"all": [{"history": "spared_redcowl"}, {"fact": "be.crates", "eq": "redcowl"}]}, "text": "Gone over the ridge with his people, and six crates nobody else is having."},
    {"when": {"history": "spared_redcowl"}, "text": "Gone over the ridge with his people, on a leg that held."},
] + c["redcowl"]
c["rav"] = [{"when": {"history": "spared_redcowl"}, "text": "Watches the ridge from his door at first light. Says it's the air."}] + c["rav"]
save("concerns.json", c)

f = load("folk.json")
f["lines"].append({"text": "Redcowl's gone off over the ridge, they say. On his own two feet. Somebody let him.", "when": {"history": "spared_redcowl"}})
save("folk.json", f)
print("applied")
