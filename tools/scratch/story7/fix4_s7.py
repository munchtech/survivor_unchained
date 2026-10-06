"""Brannoc's dusk call keyed to the scene playing (scene.now), with a night variant; Jory home,
Holloway's nearest thing to a laugh; the arrival morning report."""
from lib_s7 import *

d = load("dialogue.json")
B = d["brannoc"]
e = next(x for x in B["entry"] if x["node"] == "dusk_call")
e["when"] = all_(fact("scene.now", "brannoc"), {"met": "brannoc"}, {"day": {"gte": 2}}, nott(flag("brannoc", "asked_nell")))
dc = B["nodes"]["dusk_call"]
dc["text"] = [
    v("The forge is banked, but Brannoc is still at the anvil, and when you pass he calls you over without looking up.", {"time": "night"}),
    v("As the light goes, the hammer at the smithy stops. Brannoc calls you over, without looking up."),
]
dc["effects"] = [setf(scene__now="")]

hn = d["holloway"]["nodes"]
hn["cb_freed_teamsters"]["text"] = (
    "(He's been drinking since dawn, and he's not hiding it.) Three in! I was on the gate. Three in, and the "
    "count's— hell, I don't know what the count is. (He sits down hard.) Don't let it go to your head. Eleven "
    "Watchmen couldn't do it. Eleven Watchmen can't do much.")
save("dialogue.json", d)

r = load("rules.json")
R = r["rules"]
i_ago = next(i for i, x in enumerate(R) if x["id"] == "arena.ago")
R.insert(i_ago, {"id": "jory.home", "once": True, "when": {"history": "freed_teamsters"}, "effect": [],
                 "report": ("The teamsters came up the Old Road at first light, thin as rakes and walking. Holloway was on the "
                            "gate, and the whole square heard him: \"Three in! Count's— hell, I don't know what the count "
                            "is!\" Harlan ran the length of the street in his apron.")})
save("rules.json", r)
print("ok")
