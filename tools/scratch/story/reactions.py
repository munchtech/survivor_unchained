"""Stage 5: people react to who you are (audit item 9): your calling, your
sex and how dangerous you have become; and Maeca, who can be more than a
friend. Intimate scenes cut away by default; with settings.intimacy "full"
they show a slot for the owner's writer, marked [explicit scene: ...]."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

D = load("dialogue.json")


def home(npc):
    return {"tam": "again"}.get(npc, "hub")


def before_home(cv):
    return len(cv["entry"]) - 1


def oneoff(npc, key, text, when, at=None, choices=None):
    """Said once, on a visit after the first, then on to the greeting."""
    cv = D[npc]
    nid = f"say_{key}"
    cv["nodes"][nid] = node(text, choices=choices, effects=[setflag(npc, f"say:{key}")], next=None if choices else home(npc))
    cv["entry"].insert(at if at is not None else before_home(cv),
                       {"when": all_(met(npc), noflag(npc, f"say:{key}"), when), "node": nid})


def calling(npc, warden, reaver, arcanist, stalker, at=None):
    text = V((arch("warden"), warden), (arch("reaver"), reaver), (arch("arcanist"), arcanist), (arch("stalker"), stalker), stalker)
    oneoff(npc, "calling", text, any_(arch("warden"), arch("reaver"), arch("arcanist"), arch("stalker")), at=at)


def greet(npc, nodeid, cond, text, at=0):
    n = D[npc]["nodes"][nodeid]
    if isinstance(n["text"], str):
        n["text"] = [{"text": n["text"]}]
    n["text"].insert(at, {"when": cond, "text": text})


strong = level(gte=8)
feared = kills(gte=1500)

# ---------------------------------------------------------------- Rook --
calling("rook",
        "You sit like you're expecting the door to come in. Watch, were you? Or wanted to be.",
        "Mind the bench. The last one your size broke it, and I made him pay for it twice.",
        "If you're going to set anything on fire, pet, do it outside. Sella's got the only warm room in the house and she charges.",
        "You came in without the door making a sound. That door always makes a sound. Do it again and I'll put a bell on you.")
oneoff("rook", "woman", "There's a bolt on the inside of your door. Use it. Not for the men; for their wives. They come up the stairs looking for Sella and they're not particular.", sex("female"))

# ------------------------------------------------------------ Holloway --
calling("holloway",
        "You stand like Watch. Who trained you? ...Never mind. I can't afford you either way.",
        "I've seen men built like you on both sides of a gate. Make sure I always know which side you're on.",
        "Spark-thrower. The last one we had set the barracks roof alight trying to light a pipe. Do your tricks outside my walls.",
        "You count the ways out when you walk into a room. So do I. One of us should be paid for it.")
oneoff("holloway", "woman", "I'd tell you it's no place for a woman out there. The last three people I said that to were men, and they're dead. So I'll say: it's no place.", sex("female"))
hub = D["holloway"]["nodes"]["hub"]["text"]
i = next(k for k, v in enumerate(hub) if v.get("when", {}).get("rel"))
hub.insert(i + 1, {"when": feared, "text": "They say you've put down more things than the fever year. Try not to put any down in my square."})
hub.insert(i + 1, {"when": strong, "text": "(He straightens when you come in, and then looks annoyed that he did.) You. What is it?"})

# --------------------------------------------------------------- Maeca --
calling("maeca",
        "A shield. Good. Don't raise it in the Hollow. To a wolf a raised arm's a raised arm.",
        "Leave the big blade at the Blind if you go near the Hollow. They can smell iron that's been used.",
        "Whatever it is you burn with, don't burn it in the Hollow. Fire's the one thing they all remember.",
        "You move like you've done this. Quiet feet. ...Pity about the boots.")

# A route that opens slowly: her respect, a little warmth, and the Pack's
# trouble settled one way or the other. Never after Greymuzzle's death.
cv = D["maeca"]
open_ = all_(time("night"), rel("maeca", "respect", gte=30), rel("maeca", "affection", gte=10),
             any_(eq("beasts.outcome", "cured"), eq("beasts.outcome", "allied")), not_(hist("killed_greymuzzle")))
cv["nodes"]["invite"] = node(
    "(She finishes her cup and stands.) I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can't.",
    [ch("I can keep quiet.", goto="blind"), ch("Not tonight.", goto="hub")],
    effects=[setflag("maeca", "invited")])
cv["entry"].insert(before_home(cv), {"when": all_(met("maeca"), noflag("maeca", "invited"), open_), "node": "invite"})
blind_fx = [setd({"maeca.lover": True}), relc("maeca", quiet=True, affection=15, trust=10),
            {"condition": {"id": "warmed", "days": 1, "note": "A night at the Hunters' Blind"}},
            {"notice": "You slept well, for once. (Warmed: +8% damage, +5% speed, one day)"}]
cv["nodes"]["blind"] = node(V(
    (eq("settings.intimacy", "full"),
     "[explicit scene: Maeca and {name}, the Hunters' Blind in the Verge at night, a lean-to of hides and a fire the size of a hat; wordless, wary, careful hands that become sure ones, frost outside and the Pack audible far off; her trust given like a held breath let go — to be written]"),
    "The Hunters' Blind is a lean-to of hides and a fire the size of a hat. She feeds it one stick at a time and doesn't talk, and then neither of you needs to. Her hands are hard and careful, the way they are with a snare. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you."),
    speaker="narrator", effects=blind_fx, next="blind_morning")
cv["nodes"]["blind_morning"] = node(V(
    (flag("maeca", "told_ashford"), "(Grey light. She's already up, barefoot in the frost, listening.) Go on, then. The wood's awake, and so's Holloway, and he'll count us both."),
    "(Grey light. She's already up, barefoot in the frost, listening to the wood.) The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round me, and the old grey one came and lay down across the way in. Kept the cold off. Kept everything off. ...That's why. That's all of why. Don't make it a story."),
    [ch("I won't.", end=True)], effects=[setflag("maeca", "told_ashford")])
mh = cv["nodes"]["hub"]["choices"]
mh.insert(len(mh) - 1, ch("Is the fire at the Blind still big enough for two?", show=all_(time("night"), flag("maeca", "invited"), not_(hist("killed_greymuzzle"))),
                          when=open_, locked="Not tonight. Not like this.", goto="blind"))
gone = cv["nodes"]["gone"]
gone["text"] = V((eq("maeca.lover", True), "You went to his house. In the dark. After I told you what he was to me. Get out of my light, and don't come to the Blind again."),
                 gone["text"])

# --------------------------------------------------------------- Wenna --
calling("wenna",
        "Steel all over and not a scrap of sense in your diet. When did you last eat a green thing? Don't lie; I can see your gums.",
        "You've had that shoulder put back by somebody who didn't know what they were doing. Twice. Sit, I'll— no, you won't sit. Fine. Limp, then.",
        "Spark-hands. Don't touch the drying racks; the last one of you set my sage alight and I smelled like a funeral for a week.",
        "You're the sort that eats standing up. It shows in the skin. Here. Chew this. Don't ask what it is.")
oneoff("wenna", "woman", "If you're ever carrying, child, there's a tea for keeping it and a tea for not. I don't ask which, and I don't tell Chid.", sex("female"))

# -------------------------------------------------------------- Harlan --
calling("harlan",
        "You've the look of a caravan guard. Good ones are rarer than salt, friend. When this is over, if Jory— when this is over, come and see me about work.",
        "Big. Good. If you find the men who took my wagons, I'll not ask you to be gentle.",
        "A mage! There's a thing I've never sold. Can it find a lost wagon? No? Then what's it for?",
        "You've quiet feet. My nephew's somewhere quiet. ...Forgive me. Everything makes me think of him.")

# ---------------------------------------------------------------- Pell --
calling("pell",
        "Armour like that costs more than most of this street. Whoever paid for it, I'd very much like to meet them.",
        "I do prefer to deal with people who could break my arm. It keeps the terms so simple.",
        "A scholar of the burning arts. Do you know, I've never once sold an arcanist anything at a profit? You people read the labels.",
        "You've been standing there longer than I noticed. I don't care for that. I'll remember it.")
oneoff("pell", "woman", "I find women drive the harder bargain. I've a theory it's because you're used to being underpaid. Do prove me right; it's so rare that I am wrong.", sex("female"))

# ----------------------------------------------------------------- Rav --
calling("rav",
        "Shield arm's longer than the other. Comes of holding a door shut. Holloway'd love you, pal; don't let him.",
        "You've broken a few noses. Your knuckles are a medical history.",
        "Spell-scorched fingertips. You'll want goose fat for that. And to stop doing it, but you won't.",
        "You counted the doors when you sat down. Old Kerchief habit. Who taught you?")
oneoff("rav", "sella", V((sex("female"), "A word to the wise: Sella charges ladies the gentleman's rate, to see if they'll notice. Notice."),
                         "A word to the wise: Sella's charging the gentleman's rate this week. It's the same as the lady's rate. She just says it slower."),
       day(gte=2))

# ---------------------------------------------------------------- Chid --
calling("chid",
        "A shield! The Order's knights carried shields with the morning painted on them. Yours has... dents. Dents are good. Dents mean it worked.",
        "There's a lot of anger in you. That's all right. The light doesn't mind anger. It's only fire with manners.",
        "You burn, don't you? Not like a candle. Like... oh. Like you. Sorry. I'll stop staring. I won't, but I'll try.",
        "You came in from the side. Nobody comes in from the side. The side's where I keep the spiders.")

# -------------------------------------------------------------- Vonnra --
calling("vonnra",
        "Shields. Gates. Walls. You believe things can be kept out, traveller. It is a lovely belief.",
        "You will break a great many things before the end. Try to choose them.",
        "You carry a fire you did not buy. Be careful whom you show it to. Some of them keep ledgers.",
        "You came to my window from the side the light does not reach. Few think to. I noticed.")

# -------------------------------------------------------------- Keegan --
calling("keegan",
        "A fellow shield! Which order? None? A free lance. The handbook has a chapter on free lances. It is very rude about them.",
        "That is a great deal of weapon. Please do not swing it near the gate. The gate is older than both of us and considerably less forgiving.",
        "Arcanist. The Vigil kept a ledger of— never mind. Good morning. It is a good morning, is it not.",
        "You have been standing there for some time. I knew. I was merely being polite. ...I did not know.")
kh = D["keegan"]["nodes"]["hub"]["choices"]
kh.insert(len(kh) - 1, ch("Does the handbook say anything about dinner?", show=rel("keegan", "respect", gte=10), once="dinner", goto="dinner"))
D["keegan"]["nodes"]["dinner"] = node(
    "Chapter eleven. Fraternisation. I have not read it. ...That is a lie. I have read it four times. The answer is no. The answer is very nearly no. Good day.",
    [ch("Goodbye.", end=True)], effects=[relc("keegan", quiet=True, affection=10)])

# --------------------------------------------------------------- Sella --
calling("sella",
        "All that steel. Takes an age to get off, I expect. I charge by the hour, love, not by the buckle.",
        "Big hands. Be gentle with them upstairs, or you'll be paying for the furniture.",
        "You're warm. Not in a nice way. Are you on fire? You're a little bit on fire.",
        "You came up behind me without a sound. Do that upstairs and you'll get a candlestick in the ear.", at=1)
oneoff("sella", "woman", "Don't look so surprised, love. You're not the first woman up those stairs and you won't be the last. Half my regulars are lonelier than you.", sex("female"), at=1)
oneoff("sella", "maeca", "Maeca Barefoot came in this morning humming. Maeca. Humming. I've a professional interest, love: who's my competition?", eq("maeca.lover", True), at=1)

# ------------------------------------------------------------- Brannoc --
calling("brannoc", "Shield's warped. Bring it. No charge for looking.", "Edge is chewed. You hit things. Good.",
        "Staff. Wood. Not my trade. ...Ferrule's loose. That is.", "Knives. Light. Still. Sharp.")

# ------------------------------------------------------------- Redcowl --
first = D["redcowl"]["nodes"]["first"]
greet("redcowl", "first", any_(strong, fact("verge.kerchief_kills", gte=12)),
      "(Every crossbow in the camp is on you, and nobody's laughing.) You're the one who's been putting my lads in the ground. Redcowl. Talk, and talk slow.")
greet("redcowl", "first", arch("arcanist"),
      "Keep your hands where I can see them, and keep them cold. The last spark-thrower in here set fire to my tent. Redcowl. You're in my camp. Talk.", at=2)
greet("redcowl", "first", arch("reaver"),
      "Ha! Look at the size of you. I've a dozen lads would follow you for the fun of it; don't make me find out which dozen. Redcowl. You're in my camp. Talk.", at=3)

# ----------------------------------------------------------- Wayfinder --
calling("wayfinder",
        "A warden. You'll hold a clearing longer than most. Mind you don't hold it after it's stopped being worth holding.",
        "A reaver. You'll go in at the front and come out the back. The maps don't care which, but I do; I sell more of them to the living.",
        "An arcanist. You'll burn brighter than most in there, and faster. I've a margin for people like you.",
        "A stalker. You'll want the maps with cover. Here, and here. Don't tell the reavers; they'll only stand in it.")

save("dialogue.json", D)

# -------------------------------------------------------------- the town --
F = load("folk.json")
F["lines"] += [
    {"when": strong, "text": "That's the one. Don't look. DON'T look."},
    {"when": feared, "text": "They say that one's killed more than the fever year did."},
    {"when": all_(strong, nothas("player.wanted")), "watch": True, "text": "Captain says to let you be. Captain says it like he's not sure."},
    {"when": sex("female"), "text": "Is that a woman in all that? Good for her. Good for her."},
    {"when": sex("female"), "child": True, "text": "Are you a lady knight? Are there lady knights?"},
    {"when": arch("arcanist"), "text": "Don't stand so near the thatch, spark-hands."},
    {"when": arch("reaver"), "night": True, "text": "Evening. Please don't hit me. Evening."},
]
save("folk.json", F)
print("reactions ok")
