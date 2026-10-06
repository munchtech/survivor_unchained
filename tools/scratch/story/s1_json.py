"""Stage 1: continuity and dead content (audit item 3)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

# ---------------------------------------------------------------- quests --
Q = load("quests.json")
Q["below"]["entries"]["grimtunnel"] = "Grimtunnel, the Boss of the Dig, stole the Ford-Warden's heart and went down, not away."
Q["vault"]["entries"]["fragment"] = "A fragment of a sigil, from the hand of someone who did not make it out. It fits one notch of the door's seven, and after dark the whole sigil wakes to it."
Q["beasts"]["entries"]["pack_led"] = "The Pack ran beside you into the Roost, and the Roost fell."
save("quests.json", Q)

# -------------------------------------------------------------- concerns --
K = load("concerns.json")
for c in K["keegan"]:
    c["text"] = c["text"].replace("only he can see", "only she can see")
# Tam's father, fetched in before the Pack came (tam/farm_told, below).
K["tam"].insert(1, {"when": eq("tam.farm", "emptied"),
                    "text": "The Pack wrecked his family's farm. His Pa slept in town that night, and is alive to complain about it."})
save("concerns.json", K)

# ------------------------------------------------------------------ folk --
F = load("folk.json")
for l in F["lines"]:
    t = l["text"]
    if t == "Buried two this week. The ground's full and the priest's a boy.":
        l["text"] = "Buried two this week. The ground's full and the priest's a fool. Says so himself."
    elif t == "They found the Aldo lad in the ditch. What was left of him.":
        # One Aldo: the watchman the wolves took at the gate.
        l["text"] = "They buried Aldo this morning. The Captain carried the front of the coffin himself."
        l.pop("night", None)
        l["when"] = eq("wolves.at_gate", True)
    elif t == "The Coyle wagons had the Aldo boy's wedding cloth on them.":
        l["text"] = "The Coyle wagons had the Oswin girl's wedding cloth on them."
    elif t == "Kerchiefs hit the Aldo farm again. Prices'll climb, you watch.":
        l["text"] = "Kerchiefs hit the Penhale farm again. Prices'll climb, you watch."
F["lines"].append({"when": eq("tam.farm", "emptied"),
                   "text": "Pack tore Tam's farm to bits. His Pa was in town, thank God. Somebody fetched him in."})
save("folk.json", F)

# ----------------------------------------------------------------- items --
I = load("items.json")
I["items"]["grimtunnels_lamp"]["lore"] = "He dropped it going down the hole at the Low Ford. It is still warm, and it is still his, and he will want it back."
save("items.json", I)

# ------------------------------------------------------------ archetypes --
A = load("archetypes.json")
A["traits"]["ember_touched"]["text"] = "Every night and every arena, the ember wakes in you a level higher."
A["traits"]["second_wind"]["text"] = "Once a night, or once an arena, a killing blow leaves you standing at half health instead."
A["traits"]["kerchief_marked"]["text"] = "The Kerchiefs count you as one of theirs. So does the Watch, on its list of faces to look out for."
save("archetypes.json", A)

# ------------------------------------------------------------------ npcs --
N = load("npcs.json")
w = N["outsiders"]["wayfinder"]
w["barks"] = [
    "Maps! Places the road forgets. Some of them it forgot on purpose.",
    "Every map on this table was drawn by someone who came back. Not always all of them.",
    "Read the oaths in the margins before you go. They are not decoration.",
    "Half an hour in there and the thing that owns it comes to see who's making the noise.",
]
save("npcs.json", N)

# ----------------------------------------------------------------- rules --
R = load("rules.json")
rules = R["rules"]
ix = {r["id"]: i for i, r in enumerate(rules)}
# The farm: whoever fetched Tam's Pa in saved a man, not a farm.
farm = rules[ix["beasts.farm"]]
farm["when"]["all"].append(not_(eq("tam.pa_in", True)))
rules.insert(ix["beasts.farm"] + 1, {
    "id": "beasts.farm_empty", "once": True,
    "when": all_(fact("beasts.severity", gte=5), nothas("beasts.outcome"), eq("tam.pa_in", True), nothas("tam.farm")),
    "effect": [
        setd({"tam.farm": "emptied"}),
        history("farm_saved", "fetched Tam's father in before the Pack hit his farm", ["beasts", "deed"], 1,
                reactions={"tam": {"affection": 25, "trust": 20}, "maeca": {"respect": 10}}),
    ],
    "report": "The Pack hit the farm past the Old Road last night: pens open, the door in splinters. Nobody was home. Tam's Pa slept on Rook's floor and swore at you through breakfast.",
})
ix = {r["id"]: i for i, r in enumerate(rules)}
# Allied is an ending of its own: a cleared stream heals the wood without
# rewriting who the Pack runs with.
clear = rules[ix["stream.clear"]]
clear["when"]["all"].append(not_(eq("beasts.outcome", "allied")))
clear["effect"].insert(0, setd({"stream.clear": True}))
rules.insert(ix["stream.clear"] + 1, {
    "id": "stream.clear_allied", "once": True,
    "when": all_(fact("blight.days_clean", gte=2), eq("beasts.outcome", "allied")),
    "effect": [
        setd({"stream.clear": True}),
        history("stream_cleared", "stopped the poison in the Thornhollow stream", ["deed", "beasts"], 2),
    ],
    "report": "Wenna came in at dawn, muddy to the knees: the stream is running clear. Your wolves were drinking from it when she left.",
})
ix = {r["id"]: i for i, r in enumerate(rules)}
sold = rules[ix["stream.clear_sold"]]
sold["effect"].insert(0, setd({"stream.clear": True}))
save("rules.json", R)

# -------------------------------------------------------------- dialogue --
D = load("dialogue.json")


def N_(c, n):
    return D[c]["nodes"][n]


def choice(c, n, frag):
    hits = [x for x in N_(c, n)["choices"] if frag in (x["text"] if isinstance(x["text"], str) else x["text"][-1]["text"])]
    assert len(hits) == 1, (c, n, frag, len(hits))
    return hits[0]


# Holloway: the crime is selling the cargo, and a fine paid clears the name.
N_("holloway", "arrest")["text"] = "You sold the Coyle cargo to a fence. Everyone in the Waystation knows it, and so do I. A hundred gold to the Watch and we'll say no more about it. Or you can leave my town."
choice("holloway", "arrest", "Pay the hundred")["effects"] = [{"gold": -100}, setd({"player.fined": True, "player.wanted": False}), relc("holloway", trust=10)]
choice("holloway", "arrest", "who paid the Kerchiefs")["effects"] = [setd({"player.wanted": False})]

# Holloway's change of heart is real: once he's open to the cure and told the
# cause, he stops paying for wolves.
cause = N_("holloway", "cause")
cause["effects"].append(iff(flag("holloway", "open_to_cure"), [setd({"bounty.stopped": True})]))
cause["text"] = V((flag("holloway", "open_to_cure"),
                   "The lamplings. Of course it's the lamplings. Then I'm done paying for pelts: I'll not pay men to put down sick dogs. Deal with the pump. I'll keep watching the road."),
                  "The lamplings. Of course it is the lamplings. Deal with the pump, and I will stop paying for pelts. I will not stop watching the road.")
bounty_stopped = eq("bounty.stopped", True)
for n in ("first", "hub"):
    b = choice("holloway", n, "about the bounty")
    b["show"] = not_(bounty_stopped)
bb = N_("holloway", "bounty")
for c in bb["choices"]:
    if c["text"] in ("Hand over the fang.", "Hand over the pelts."):
        c["show"] = not_(bounty_stopped)

# Harlan: Jory is home, and standing at the stall.
for n in D["harlan"]["nodes"].values():
    for c in n.get("choices", []):
        if c["text"] == "Jory is alive. He is on his way.":
            c["text"] = "Jory's alive. He's home."
hub = N_("harlan", "hub")
hub["text"][0]["text"] = "Jory's round the back, pretending to count crates. Pretending! What can I do for you, friend?"

# Rook: the trunk stood beside Ashe's stone; he was never dug up.
N_("rook", "firstlamp")["text"] = "You found old Ashe, and his trunk. Captain of the first Watch, when it was forty lamps and not four. This inn is named for his: the Last Lamp, because it was the last one lit on the night they closed the north road. We light the hearth from it every winter. Keep what was in the trunk; he'd have wanted it used. Just leave him where he lies."

# Keegan's tenses.
N_("keegan", "ashe")["text"] = "Know him? The Vigil buried him. He closed the north road with forty lamps and walked back through it with one. What he saw up there is why I am standing here telling you no. Were he here, he would tell you himself, once you were ready."

# The Wayfinder: a won arena is noticed, and the arenas are described as they are.
wh = N_("wayfinder", "hub")
wh["text"][0]["when"] = fact("arena.won", gte=1)
N_("wayfinder", "oaths")["text"] = "Every map is sworn under something, written in the margin: the Long Winter, the Blight, Iron, a shorter light. The place keeps its oath, and so will you, whether you read it or not. A cold place pays out in things that keep the cold off. Go in dressed for it, or come out dressed for it. Those are the choices."
N_("wayfinder", "places")["text"] = "Half an hour, give or take, and it only gets worse. The ember in you starts from nothing in there, same as every night. Last the half hour and whatever rules the place comes out to see who's been killing its people. Kill it and the way out opens where it fell. Stay past that if you like. Some do. I sell them fewer maps."

# Tam's directions mean something: with them, his Pa can be fetched in.
again = N_("tam", "again")
again["choices"].insert(1, ch("Your farm's past the Old Road, you said. I'll fetch your Pa in before dark.",
                              show=all_(flag("tam", "farm_told"), fact("beasts.severity", gte=2), nothas("tam.farm"),
                                        nothas("beasts.outcome"), not_(eq("tam.pa_in", True))),
                              goto="fetch"))
D["tam"]["nodes"]["fetch"] = node(
    "You walk the boy as far as the fence where his Pa lost the goat, and his Pa out of the trees on the other side. He calls you several things on the way, and one of them is a fool. He comes.",
    speaker="narrator",
    effects=[setd({"tam.pa_in": True}), relc("tam", trust=20, affection=15)],
    choices=[ch("Stay by the well, Tam.", end=True)])

# The board: a bounty withdrawn by a man who changed his mind.
board = N_("board", "read")
for v in board["text"]:
    if v["text"].startswith("WOLF BOUNTY"):
        v["when"] = all_(nothas("beasts.outcome"), not_(bounty_stopped))
idx = next(i for i, v in enumerate(board["text"]) if v["text"].startswith("WOLF BOUNTY"))
board["text"].insert(idx + 1, {"when": all_(nothas("beasts.outcome"), bounty_stopped), "add": True,
                               "text": "The wolf bounty is SUSPENDED. The Watch will not pay for pelts. Capt. Holloway. (Underneath, in another hand: \"why??\")"})
save("dialogue.json", D)
print("stage 1 ok")
