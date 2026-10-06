"""Second pass, darker: the cost of things lands, and two secrets cast a longer shadow."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

def before_last(lst, item):
    lst.insert(len(lst) - 1, item)

# ----------------------------------------------------------------- rules --
R = load("rules.json")
rules = R["rules"]
by = {r["id"]: r for r in rules}

by["beasts.gate"]["report"] = "Wolves at the east gate in the night, a dozen of them, sick and bold. They had Aldo off the wall by his bad leg before anyone heard him shout. The Watch found most of him in the morning."
by["beasts.gate"]["effect"].append({"later": {"days": 1, "id": "aldo.buried", "effect": setd({"aldo.buried": True})}})
by["caravan.starve"]["report"] = "Word from the Old Road: the Kerchiefs have stopped feeding their prisoners. Somebody heard them through the trees, asking for water. Harlan has not come out of his shop."
by["caravan.starve"]["effect"].append({"later": {"days": 1, "id": "caravan.bodies", "effect": setd({"caravan.bodies": True})}})
by["chapter.ready"]  # unchanged

new = [
    {"id": "aldo.buried", "once": True, "when": eq("aldo.buried", True), "effect": [],
     "report": "They buried Aldo in the Watch's corner of the yard. Holloway read the words himself and got two of them wrong, and nobody corrected him. His wife is coming up from Low Kiln. Somebody will have to tell her about the leg."},
    {"id": "caravan.bodies", "once": True, "when": all_(eq("caravan.bodies", True), not_(hist("burned_roost"))), "effect": [],
     "report": "Holloway's men brought the teamsters back from the ravine on a cart, under sacking. There were three. Harlan walked behind it all the way to the shrine, and when Chid lifted the sacking Harlan made a sound nobody on the square will forget."},
    {"id": "roost.ash", "once": True, "when": hist("burned_roost"), "effect": [],
     "report": "Smoke from the ravine all night, and the smell came over the wall with it. Rook burned rosemary in every room. Harlan has nailed his shutters closed from the inside."},
    {"id": "dig.burned", "once": True, "when": eq("dig.pump", "blown"), "effect": [],
     "report": "The Watch says the lamplings were carrying their own out of the hillside all night: small, and burned, some still holding their lamps lit. One of them sat by the pile and counted them. It got to forty and started again."},
    {"id": "jory.nights", "once": True, "when": hist("freed_teamsters"), "effect": [],
     "report": "Jory Coyle woke the inn twice in the night, shouting for a man called Ewan. Rook sat with him until it was light. Ewan was in the fourth cage, he says. There isn't a fourth cage any more."},
    {"id": "shrine.bell", "once": True, "when": eq("shrine.lit", True), "effect": [],
     "report": "Chid rang the shrine bell at first light, for the first time anyone can remember. Half the town came out thinking it was a fire. The other half came out because it wasn't."},
    {"id": "pelts.stacked", "once": True, "when": hist("wolf_slaughter"), "effect": [],
     "report": "Brannoc's yard is stacked with pelts to the eaves, and the flies have found it. Maeca walked past it this morning and did not look."},
]
ix = rules.index(by["chapter.ready"])
for r in reversed(new):
    rules.insert(ix, r)
save("rules.json", R)

# -------------------------------------------------------------- dialogue --
D = load("dialogue.json")
N = lambda c, n: D[c]["nodes"][n]

# Harlan: the grief, and the guilt under it.
hub = N("harlan", "hub")["text"]
for v in hub:
    if v.get("when") == eq("caravan.survivors", "dead"):
        v["text"] = "I heard. I heard. ...They'd not been fed for a week, Holloway says. Jory used to sulk if supper was late. You needn't say anything. What do you want?"
N("harlan", "ash")["text"] = "They said there was screaming. Was there screaming? ...They said you could smell it from the wall. No. Don't tell me. Just don't come to my stall again. Don't come to the funeral. There's nothing to bury."
before_last(N("harlan", "hub")["choices"], ch("How's Jory?", show=eq("caravan.survivors", "rescued"), once="jory_now", goto="jory_now"))
D["harlan"]["nodes"]["jory_now"] = node(
    "Sleeps with the lamp lit. Eats like a horse. Asked me last night what was in the crates. I told him salt. He believed me; he always does. ...That's the worst of it, friend. He always does.",
    [ch("Something else.", goto="hub"), ch("Goodbye.", end=True)])

# Holloway: Aldo is a person.
for v in N("holloway", "hub")["text"]:
    if v.get("when") == eq("wolves.at_gate", True):
        v["text"] = "You heard. Aldo. Wife at Low Kiln, a bad knee, and a habit of humming on the wall that I told him twice to stop. They took him off it by the bad leg. I'd give a month's pay to hear him hum. Five a pelt, still. What do you want?"

# Vonnra: the shadow gets longer.
vh = N("vonnra", "hub")["text"]
vh.insert(1, {"when": time("night"), "text": "(Her lamp is lit, and she is looking south, toward the ford.) Traveller. The road was quiet tonight. It will not always be. Payment, always."})
before_last(N("vonnra", "hub")["choices"], ch("That coin on the cord at your throat?", once="coin", goto="coin"))
D["vonnra"]["nodes"]["coin"] = node(
    "Old-empire. Square. My grandmother's, and hers before. I have never spent it. One day I shall, and it will buy something that cannot be bought twice. ...That was free. Do not grow used to it.",
    [ch("Something else.", goto="hub"), ch("Goodbye.", end=True)])
D["vonnra"]["nodes"]["risen"] = node(
    "You came back. Most do not, the first time. ...Do not thank Chid. Do not thank anyone. Payment, always, traveller, and for that above all; you will find out who holds the note.",
    effects=[setflag("vonnra", "say:risen")], next="hub")
D["vonnra"]["entry"].insert(len(D["vonnra"]["entry"]) - 1,
                            {"when": all_(met("vonnra"), trait("risen_once"), noflag("vonnra", "say:risen")), "node": "risen"})

# Chid: what the ember takes, said by the one who knows.
D["chid"]["nodes"]["names"] = node(
    "Can I ask you something? Your mother's name. ...No, don't tell me. You had to think. I saw you think. Write the names down, somewhere you'll find them. It always takes the names first. Then the faces. I'm sorry. I'll stop. Sit, sit.",
    effects=[setflag("chid", "say:names")], next="hub")
D["chid"]["entry"].insert(len(D["chid"]["entry"]) - 1,
                          {"when": all_(met("chid"), day(gte=3), noflag("chid", "say:names")), "node": "names"})

# The Dig eats its own.
before_last(N("snib", "hub")["choices"], ch("What happens to the pipe-lads?", once="pipelads", goto="pipelads"))
D["snib"]["nodes"]["pipelads"] = node(
    "Pipe-lads go blind by spring. Then deaf. Then they go in the slurry, because it is warm, and they do not come out. Snib was a pipe-lad. Snib got promoted. ...Snib does not want to talk about pipe-lads. Snib wants you to LEAVE.",
    [ch("Leave.", end=True)])
N("survivor", "what")["text"] = "Down there. Under the one that is dead. There is another. There is always another. Kell went down to see. Kell's lamp came back up on its own, still lit. Still lit. Take the map, take it, I do not want to know where the tunnels go any more."

# The board remembers Aldo.
board = N("board", "read")["text"]
i = next(k for k, v in enumerate(board) if v["text"].startswith("CURFEW"))
board.insert(i + 1, {"when": eq("wolves.at_gate", True), "add": True,
                     "text": "AT REST: Aldo Penn, of the Watch, twenty-two years on the walls. A collection for his widow at the Watch House. (Underneath: \"he hummed\")"})
save("dialogue.json", D)

# ------------------------------------------------------------------ folk --
F = load("folk.json")
F["lines"] += [
    {"when": hist("burned_roost"), "text": "They say you could hear them from the ridge. The ones in the cages. They say it went on a while."},
    {"when": hist("prisoners_died"), "text": "Harlan stood at the graves the whole afternoon. Didn't say a word. Didn't take his hat off, either. Forgot he had it on."},
    {"when": eq("dig.pump", "blown"), "night": True, "text": "You can still see their lamps up on the hill at night. Fewer every night."},
]
save("folk.json", F)
print("dark ok")
