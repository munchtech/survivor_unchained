"""Act 1 rewrite, part B: Brannoc (notes 01 item 7, the owner's choices).
- his pride planted on day 1 (the irons, her boots, "walk where it's lit");
- C07 reordered: the mercy before the knife; his iron in his hands; "She'd have thought I'd come
  for her."; "Forge is shut."; then his lantern: "You know the place." (C07 and C14 one sequence);
- C07 plays at dusk in the town (a scene), so she does not have to go to him;
- the road: his hand round the last light; the road dark and the hammer slow after (no forge
  closed, no cost at the bench: the truth must never cost more than the lie)."""
from lib_s7 import *

d = load("dialogue.json")
B = d["brannoc"]
bn = B["nodes"]

pride = " (The hammer. He looks at you properly.) ...Came up the Low Ford road? Irons on it. Mine. Ten. (The hammer.) Best I've done."
bn["first"]["text"][0]["text"] = "Hunter. Good. You'll know a clean pelt. Brannoc. Iron, and things with fur on." + pride
bn["first"]["text"][1]["text"] = "Brannoc. I make things of iron. I buy things with fur on. Which?" + pride

bn["irons"]["text"][1]["text"] = (
    "Spares. Twelve ordered for the Low Ford, last winter. Ten collected, at night, coin left on the anvil. "
    "Old coin. Square. (He runs his thumb along one.) Didn't ask who. Paid for my girl's boots.")
bn["mark"]["text"][1]["text"] = (
    "(He takes it. Turns it to the light. Puts his thumb under the socket.) Mine. Mark's under there. (He "
    "weighs it.) Thing in the water had it? ...Took it off a post, then. Good iron. Held. (He gives it "
    "back.) Keep it. It'll hold.")
bn["hub"]["text"][2]["text"] = (
    "(He works one-handed; the other hand is bound in rag. He doesn't stop when you come in, and he doesn't "
    "send you away.) Steel or fur?")
assert "nell.buried" in str(bn["hub"]["text"][2]["when"])

# C07, reordered: the mercy first, then his own work in his hands.
bn["nell_ditch"]["text"] = bn["nell_ditch"]["text"][1]["text"]
bn["nell_gone"] = node("nell_gone", "Quick, then. Water's quick. (He picks the hammer up and holds it, and doesn't use it.)", nxt="nell_iron")
bn["nell_quick"] = node("nell_quick", "(A long time.) ...Thank you.", nxt="nell_iron")
bn["nell_slow"] = node("nell_slow", "(He nods, once, as if you've told him a price.)", nxt="nell_iron")
has = {"hasItem": "wardens_lampiron"}
saw = fact("brannoc.saw_iron", True)
knew = [setf(brannoc__knew_iron=True),
        {"quest": {"id": "lamps", "status": "active", "entry": "irons"}}, {"quest": {"id": "lamps", "entry": "mark"}}]
put_nodes(B,
    node("nell_iron", [
        v("(His eyes go to the iron at your belt, and stay there.) ...That was in its hand. The thing in the water.", all_(has, saw)),
        v("(His eyes go to the iron at your belt, and stay there.) ...Where'd you get that.", has),
        v("(He looks at the two irons on the rack, and then at you.) The thing in the water. What was it carrying."),
    ], choices=[
        ch("Yes.", "nell_hand", show=all_(has, saw)),
        ch("Out of the fist of the thing in the ford.", "nell_hand", show=all_(has, nott(saw))),
        ch("A lamp-iron. Your mark under the socket.", "nell_told", show=nott(has)),
    ]),
    node("nell_hand", (
        "(He holds out his hand. You put the iron in it. He turns it to the forge, and his thumb goes under the "
        "socket and finds the mark without looking.) Lifts it up. (a breath) To see your face. ...Does it."),
        choices=[ch("It does.", "nell_letters")]),
    node("nell_told", "(He doesn't move.) Lifts it up. (a breath) To see your face. ...Does it.",
         choices=[ch("It does.", "nell_letters")]),
    node("nell_letters", "(The forge ticks. He does not move for a long time.) Knew my mark before she knew her letters.",
         effects=knew, nxt="nell_thought"),
    node("nell_thought", "(Longer.) She'd have thought I'd come for her.", nxt="nell_shut"),
    node("nell_shut", [
        v("(Nothing. Then he gives you the iron back, carefully, the way you'd hand someone a thing that was still hot. "
          "On the anvil the bar goes from orange to grey.) Forge is shut.", has),
        v("(Nothing. On the anvil the bar goes from orange to grey.) Forge is shut."),
    ], nxt="nell_lantern"),
    node("nell_lantern", "(He takes the lantern down off its hook, and lights it, and takes a blanket off the shelf.) You know the place.",
         choices=[ch("I'll show you.", "nell_with", effects=[setf(nell__road="with")]),
                  ch("Not tonight.", "nell_alone", effects=[setf(nell__road="alone")])]),
    node("nell_with", (
        "He doesn't wait for anything else. He goes out, and you go with him, down toward the south gate in the "
        "last of the light."), speaker="narrator", choices=[ch("(Go with him.)", end=True)]),
    node("nell_alone", "He nods, once, and goes out past you with the lantern and the blanket, down toward the south gate.",
         speaker="narrator", choices=[ch("(Let him go.)", end=True)]),
    # The forge at dusk: he calls her over (the scene the town's dusk plays, Journey.TakeScene).
    node("dusk_call", "As the light goes, the hammer at the smithy stops. Brannoc calls you over, without looking up.",
         speaker="narrator", nxt="nell"),
)
# Its entry, before the day's: at dusk, on the day he would ask.
i = next(i for i, e in enumerate(B["entry"]) if e["node"] == "nell")
nell_when = B["entry"][i]["when"]
B["entry"].insert(i, {"when": all_({"time": "dusk"}, nell_when), "node": "dusk_call"})

save("dialogue.json", d)

# Barks: his pride, until he knows; the hoping, on the lie.
n = load("npcs.json")
said = n["npcs"]["brannoc"]["said"]
unknown = nott(fact("nell.told", exists=True))
said += [
    {"text": "Girl's first new boots. Irons paid for 'em.", "night": False, "when": unknown},
    {"text": "Told her: walk where it's lit. Nothing on that road you can't see.", "night": False, "when": unknown},
    {"text": "Pedlar says the Kiln road's dry. Good.", "night": False, "when": any_(fact("nell.told", "lie"), fact("nell.told", "evaded"))},
]
save("npcs.json", n)

# The road, the burial, the dark road after. And the forge at dusk as a scene.
r = load("rules.json")
R = r["rules"]
i = next(i for i, x in enumerate(R) if x["id"] == "nell.burial")
old = R[i]
told = old["when"]
with_ = {"id": "nell.burial_with", "once": True, "when": all_(told, fact("nell.road", "with")),
         "effect": old["effect"] + [{"later": {"days": 1, "id": "brannoc.road_dark", "effect": [setf(brannoc__road_dark=True)]}}],
         "report": (
             "You walked down the Low Ford road with Brannoc in the last of the light, between his irons, and he never "
             "once looked up at them. Under the last one, over the ditch, he stopped. He reached up and closed his bare "
             "hand round the light until it went out, and made no sound, and opened his hand. Then he got down into the "
             "ditch for her. Two small new boots stuck out of the blanket's end all the way home. They are burying her "
             "this morning, behind the shrine, next to the old captain.")}
alone = {"id": "nell.burial", "once": True, "when": all_(told, nott(fact("nell.road", "with"))),
         "effect": old["effect"] + [{"later": {"days": 1, "id": "brannoc.road_dark", "effect": [setf(brannoc__road_dark=True)]}}],
         "report": (
             "Last night Brannoc's lantern went down the blue road alone, small, between his irons. At the ford one blue "
             "light went out. He came back up the road at sunrise with the blanket in his arms, and Chid walked out past "
             "the guards to meet him, and walked beside him up the street. They are burying her this morning, behind the "
             "shrine, next to the old captain. Nobody has been asked to come.")}
R[i:i + 1] = [with_, alone]
R.insert(i + 2, {"id": "brannoc.road_dark", "once": True, "when": fact("brannoc.road_dark", True), "effect": [],
                 "report": ("The Low Ford road was dark at dawn, for the first time since winter: every iron on it out. And "
                            "the hammer's wrong. It comes slower now, one-handed, with a beat missing, and you can hear the "
                            "river from the square.")})
i_ago = next(i for i, x in enumerate(R) if x["id"] == "arena.ago")
R.insert(i_ago, {"id": "brannoc.forge", "once": True,
                 "when": all_({"day": {"gte": 2}}, {"met": "brannoc"}, nott(flag("brannoc", "asked_nell")), nott(fact("scene.dusk", exists=True))),
                 "effect": [setf(scene__dusk="brannoc:dusk_call")]})
save("rules.json", r)
print("ok")
