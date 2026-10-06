"""Stage 4: named people quote your deeds back (audit item 5).

A callback is an entry that fires the first visit after a deed is known,
once (a cb:<event> flag on the person), then hands on to their greeting.
A few deeds close a door for good instead (Harlan after the Roost burned,
Maeca after Greymuzzle died in his own Hollow)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

D = load("dialogue.json")


def home(npc):
    return {"tam": "again"}.get(npc, "hub")


def last_entry_index(cv):
    """Before the conversation's fallback (the last, unconditional entry)."""
    return len(cv["entry"]) - 1


def callback(npc, ev, text, when=None, choices=None, extra=None, effects=None, at=None):
    cv = D[npc]
    key = f"cb:{ev}"
    nid = f"cb_{ev}"
    cond = all_(when if when is not None else hist(ev), met(npc), noflag(npc, key))
    eff = [setflag(npc, key)] + (effects or [])
    n = node(text, choices=choices, effects=eff, next=None if choices else home(npc))
    assert nid not in cv["nodes"], nid
    cv["nodes"][nid] = n
    for k, v in (extra or {}).items():
        cv["nodes"][k] = v
    cv["entry"].insert(at if at is not None else last_entry_index(cv), {"when": cond, "node": nid})


def door_shut(npc, nid, cond, text, at):
    """A deed that ends the relationship: every visit, from now on."""
    D[npc]["nodes"][nid] = node(text, [ch("...", end=True)])
    D[npc]["entry"].insert(at, {"when": cond, "node": nid})


back = lambda: ch("Something else.", goto="hub")

# ---------------------------------------------------------------- Harlan --
door_shut("harlan", "ash", hist("burned_roost"),
          "They said there was screaming. Was there screaming? ...No. Don't tell me. Just don't come to my stall again.", 0)
callback("harlan", "exposed_pell",
         "Holloway showed me Pell's book. Payments to \"R.\", on the night. I sat at that man's table at midsummer and let him pour my wine. ...Thank you. I think. I'll know when I've stopped feeling sick.",
         when=all_(hist("exposed_pell"), noflag("harlan", "once:pell")))
callback("harlan", "sold_dig",
         "Word is you sold Pell what the Dig was doing to the stream, and he sold it on. ...Well. I've sold worse, to worse. Don't look at me like that, friend; I'm agreeing with you.",
         when=nk("harlan", "sold_dig"))
callback("harlan", "killed_greymuzzle",
         "They say the old grey wolf's dead. It wasn't wolves that took my wagons, I know that now. But it was wolves on that road every other night, and I'll not pretend to weep.")

# -------------------------------------------------------------- Holloway --
callback("holloway", "killed_greymuzzle", V(
    (eq("bounty.stopped", True), "I hear you put the old grey one down. I'd stopped paying for it. You did it anyway. I'm trying to work out what that makes you."),
    "Greymuzzle's dead, they tell me. Maeca won't speak to me for a month and I've slept better for it already. ...Twenty years that wolf's had the run of this valley. Odd, missing a thing you hated."))
callback("holloway", "burned_roost",
         "The Roost burned with the cages full. I've hanged men for less. I can't prove you lit it, and you know I can't, and I'd like you to know that I know that.",
         effects=[relc("holloway", quiet=True, trust=-10)])
callback("holloway", "freed_teamsters",
         "Three teamsters walked in through my gate, thin as rakes and alive. You did what eleven Watchmen couldn't. Don't let it go to your head; eleven Watchmen can't do much.")
callback("holloway", "tricked_redcowl",
         "Somebody told Redcowl the Watch was coming, and he ran. The Watch was in bed. ...I'd ask you not to use my name in vain. But it worked. Did it work? It worked.")
callback("holloway", "opened_vault",
         "You went through the black door. The Watch was founded on the promise that nobody would. My predecessors would've hanged you for it. I'm too tired. What's down there?",
         choices=[ch("A stair. Going down.", goto="cb_vault2"), ch("Nothing you'd want.", goto="cb_vault2")],
         extra={"cb_vault2": node("Course it is. Keep it to yourself. I've enough to count.", [back(), ch("That's all.", end=True)])})
callback("holloway", "nemesis_slain",
         "Heard you went back for whatever killed you and took your things off it. I've known men who wouldn't go back for their own boots.")
callback("holloway", "core_stolen",
         "They say a lampling walked off with the Warden's heart while you stood there. Don't tell me why you let it. I've a feeling I'd not like either answer.",
         when=all_(hist("core_stolen"), day(gte=2)))

# ------------------------------------------------------------------ Rook --
callback("rook", "shrine_lit",
         "Chid came running in this morning without his shoes on. The shrine lamp, he says. My mother's lamp's got a sister again. ...Your bowl's on the house tonight. Don't make a habit of it.",
         effects=[relc("rook", quiet=True, affection=5)])
callback("rook", "freed_teamsters",
         "Jory Coyle's in my good room, and Harlan's tried to pay me for it twice. You've a lot to answer for, pet, bringing that much crying into one house.")
callback("rook", "burned_roost",
         "There were people in those cages. ...I'll take your money. I'll not have you in my kitchen.")
callback("rook", "nemesis_slain",
         "You went back for your things. Good. Never let anything keep what's yours; it only teaches it to take more.")
callback("rook", "opened_vault",
         "You smell of cold stone. Don't tell me where you've been. Chid'll tell me anyway, and get it wrong.")

# ----------------------------------------------------------------- Maeca --
door_shut("maeca", "gone", hist("killed_greymuzzle"), "You went to his house. In the dark. Get out of my light.", 2)
callback("maeca", "burned_roost",
         "You burned the Roost with them still in the cages. I know what fire does in a ravine. I was at Ashford.")

# ------------------------------------------------------------------- Rav --
callback("rav", "tricked_redcowl",
         "You told Redcowl the Watch was coming, and he RAN. I've waited eleven years to see that man run. Sit. This one's on me, and so's the next.",
         effects=[relc("rav", quiet=True, affection=5)])
callback("rav", "killed_redcowl",
         "(He doesn't look up.) You killed him. ...No. He'd have said it was the job. It was always the job, with him. Get out of my light for a bit, pal. Come back tomorrow. I'll be a doctor again tomorrow.",
         choices=[ch("...", end=True)])
callback("rav", "burned_roost",
         "The Roost burned. With the cages full, they're saying. ...He'll have got out. He always gets out. The ones in the cages didn't.")
callback("rav", "exposed_pell",
         "Pell in irons! I'll drink to that. I'll drink to anything, but I'll drink to that twice.")

# ------------------------------------------------------------------ Chid --
callback("chid", "opened_vault",
         "You went through the door! You went through— what was on the stair? No, don't tell me. Yes, tell me. No.",
         choices=[ch("A stair going down. And the dead, coming up it.", goto="cb_vault2"), ch("I'd rather not say.", goto="hub")],
         extra={"cb_vault2": node("Then they're still keeping it. Good. Good, I think. ...I'm going to light every candle I've got.", [back(), ch("Goodbye.", end=True)])})
callback("chid", "core_stolen",
         "The Warden's heart. Rook says a lampling took it at the ford. ...Oh, dear. Oh, dear, dear. That was one of the old ones. They're not meant to be carried about.")
callback("chid", "nemesis_slain",
         "You got your things back! From the thing! Was it horrible? It was horrible. Sit down. Not there. There.")

# ---------------------------------------------------------------- Vonnra --
callback("vonnra", "opened_vault",
         "You opened it. ...Do not sit, traveller. I would rather you stood. What did you see on the stair?",
         choices=[ch("A stair going down. The dead coming up it.", goto="cb_vault2"), ch("That's mine to know.", goto="cb_vault3")],
         extra={"cb_vault2": node("Then it is still there. That is all. I will say it again, because it bears repeating: that is all.", [ch("Goodbye.", end=True)]),
                "cb_vault3": node("It is. For now. Payment, always, traveller; even for silence. You will find I collect.", [ch("Goodbye.", end=True)])})
callback("vonnra", "core_stolen",
         "A heart went into the ground at the Low Ford, and you watched it go. I am not angry. I am arranging.",
         when=all_(hist("core_stolen"), day(gte=2)))
callback("vonnra", "exposed_pell",
         "Pell Varrow in irons. He owed me a great deal. I shall have to find another way to be paid.")

# ---------------------------------------------------------------- Keegan --
callback("keegan", "opened_vault",
         "You opened the black door. The handbook has a chapter on that. It is a short chapter. It is the word \"don't\", in several sizes.")
callback("keegan", "core_stolen",
         "The Warden's heart, taken at the ford. ...I am going to write to the chapterhouse. Again. Twice, perhaps. In capitals.",
         when=all_(hist("core_stolen"), knows("lore.warden")))

# ----------------------------------------------------------------- Wenna --
callback("wenna", "sold_dig",
         "You sold it. The stream, the Pack, all of it, to Pell, for forty. I tested that water for you, child. ...I'll still sell you an antidote. I'll charge you double, and I'll enjoy it.",
         when=nk("wenna", "sold_dig"))
callback("wenna", "broke_pump",
         "You stopped their pump. I can smell the difference already. Don't argue; I can.",
         when=any_(hist("broke_pump"), hist("blew_dig")))
callback("wenna", "shrine_lit",
         "Chid's lamp's lit. He came to tell me with his shoes on the wrong feet.")

# ----------------------------------------------------------------- Sella --
# Before her "again" (a regular is greeted as one), so they are heard at all.
_cb = callback
callback = lambda *a, **k: _cb(*a, at=1, **k)
callback("sella", "tricked_redcowl",
         "Heard you sent Redcowl running with nothing but a lie and a straight face. You'd do well upstairs, love.")
callback("sella", "exposed_pell",
         "Pell's in the cells. One less customer. I'll miss his money and not one other thing about him.")
callback("sella", "burned_roost",
         "They're saying you burned the Roost with folk still in it. ...I don't judge, love; it's bad for business. But I heard.")
callback("sella", "freed_teamsters",
         "Jory Coyle came up the stairs to say thank you to somebody, and it wasn't me, and he went red as a radish. Sweet. Go easy on him; he thinks you're a story.")

# ------------------------------------------------------------------ Pell --
callback = _cb
callback("pell", "tricked_redcowl",
         "I hear the Kerchiefs left their camp in rather a hurry. On your word. How very... efficient.")

# --------------------------------------------------------------- Brannoc --
callback("brannoc", "killed_greymuzzle", "Grey one's dead. Should've brought him here. Fang like that.")
callback("brannoc", "wolf_slaughter", "Lot of pelts. Lot of wolves. Wood'll be quiet.")

# ------------------------------------------------------------------- Tam --
callback("tam", "killed_greymuzzle",
         "Did you kill the big grey one? ...Was he sick too?",
         choices=[ch("He was sick.", goto="cb_grey2"), ch("He was dangerous.", goto="cb_grey2")],
         extra={"cb_grey2": node("Oh. ...Pa says you have to, sometimes. Pa says a lot of things.", [ch("Stay by the well, Tam.", end=True)])})

# ------------------------------------------------------------- Wayfinder --
callback("wayfinder", "nemesis_slain",
         "You went back for whatever killed you, and took your things off it. That's going in a margin. People like reading about that.")
callback("wayfinder", "opened_vault",
         "You've been under the black door. Don't tell me what's on the stair; I'd only have to draw it, and I don't draw that far down.")

save("dialogue.json", D)
print("callbacks ok")
