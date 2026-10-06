"""Second pass, adult: frank talk, the right mouths swearing, and Sella off the clock."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

D = load("dialogue.json")
N_ = lambda c, n: D[c]["nodes"][n]


def before_last(lst, item):
    lst.insert(len(lst) - 1, item)


# Holloway swears once, where it counts.
N_("holloway", "liar")["text"] = N_("holloway", "liar")["text"].replace("spend the night in the cells.", "spend the night in the fucking cells.")
N_("holloway", "defied")["text"] = "Out of my sight. And if I see you near my gate with a blade out, you'll find out how the cells feel on a cold night, and how the cell-rats feel about fresh meat."

# Rav: a doctor's mouth.
rh = N_("rav", "hub")["text"]
for v in rh:
    if v.get("when") == time("night"):
        v["text"] = "Night surgery's double. Night drinking's the same price; I checked. And if you're here for Sella, she's busy: you can hear the bed from the cellar."
before_last(N_("rav", "hub")["choices"], ch("Doctor, I've a pain.", show=all_(time("night"), rel("rav", "trust", gte=20)), once="pain", goto="pain"))
D["rav"]["nodes"]["pain"] = node(
    "Where? ...No, don't point, pal, we're in company. Come round the back after closing and I'll take a look. Largely professionally. Bring a bottle; it's an anaesthetic for one of us.",
    [ch("Another night, Doctor.", goto="hub"), ch("Goodbye.", end=True)], effects=[relc("rav", quiet=True, affection=5)])

# Redcowl: a threat you can picture.
rf = N_("redcowl", "first")["text"]
rf.insert(len(rf) - 1, {"when": sex("female"),
                        "text": "Well. My lads haven't seen a woman who wasn't their mother in a month, nor a bath in a year. Walk straight and they'll keep their hands where I've told them. Redcowl. You're in my camp. Talk."})
before_last(N_("redcowl", "hub")["choices"], ch("Why keep them in cages?", once="cages", goto="cages"))
D["redcowl"]["nodes"]["cages"] = node(
    "Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. I've buried enough worth-nothings for one life, lad. ...And I feed them. Ask them. I feed them before I feed my own.",
    [ch("About the Coyle wagons.", goto="goods"), ch("Nothing.", end=True)])

# Sella: off the clock. A lover who warns you about herself.
S = D["sella"]
S["nodes"]["free"] = node(
    "Put your purse away, {name}. Tonight I'm not working. ...Don't look at me like that. Don't make it strange.",
    [ch("Then lead the way.", goto="free_night"), ch("Not tonight, Sella.", goto="hub")],
    effects=[setflag("sella", "say:free")])
S["nodes"]["free_night"] = node(V(
    (eq("settings.intimacy", "full"),
     "[explicit scene: Sella and {name}, the blue room, not for money for the first time; slower and less sure than her working nights, the professional's patter dropping away, laughter and then none; a door she locks herself — to be written]"),
    "The blue room, and the lamp, and the bolt, which she shoots herself, which she has never done. She doesn't talk the way she talks for money. For a while neither of you talks at all. Later she lies awake and you can feel her deciding something, and then she sleeps."),
    speaker="narrator", next="free_morning",
    effects=[setd({"sella.free": True}), relc("sella", quiet=True, affection=10, trust=10),
             {"condition": {"id": "warmed", "days": 1, "note": "A night in the blue room, off the clock"}}])
S["nodes"]["free_morning"] = node(
    "(She's still there when you wake, which she never is.) Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anything up here you'd not want Vonnra to hear. I mean that kindly. It's the kindest thing I've said to anyone in a year.",
    [ch("Until next time.", end=True)])
S["entry"].insert(1, {"when": all_(met("sella"), time("night"), fact("sella.nights", gte=3), rel("sella", "affection", gte=25), noflag("sella", "say:free")), "node": "free"})
for v in N_("sella", "hub")["text"]:
    if v.get("when") == time("night"):
        v["text"] = "Evening, {name}. The lamp's lit upstairs, if you're asking. You look like you're asking. You look like you've been asking all day."
save("dialogue.json", D)

N = load("npcs.json")
N["npcs"]["rav"]["barks"].append("Pox, piles, a pike-wound or a broken heart: I've a cure for three of them and a drink for the fourth.")
N["npcs"]["sella"]["nightBarks"].append("Rook's walls are thin and I'm not quiet. Fair warning.")
N["outsiders"]["redcowl"]["barks"].append("Last man who lied to me, I nailed his tongue to a cart and let the horse decide.")
save("npcs.json", N)

F = load("folk.json")
F["lines"] += [
    {"night": True, "text": "Sella's got a new customer, the walls are saying. The walls are very specific."},
    {"text": "The Flagon's piss is cheaper than the Flagon's ale, and honestly? You can't tell."},
    {"text": "My wife ran off with a tinker. Best thing that ever happened to the tinker."},
    {"text": "Kerchief lad tried his luck with my daughter. She broke his nose with a bucket. Never been prouder."},
    {"night": True, "text": "If you're going to throw up, do it in the trough. The horses have seen worse."},
    {"watch": True, "text": "Indoors, before I find a reason. I'm good at finding reasons."},
    {"when": eq("sella.free", True), "text": "Sella was singing on the stairs this morning. Sella. Singing. Somebody's in trouble."},
]
save("folk.json", F)
print("adult ok")
