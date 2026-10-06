"""Fixes after the first test run: the scenes' speakers; the burial keeps its opening; the
fortune's third reading picks what mattered most (her bought past, then the crates, then Pell);
the chapter is not held on the knocking (Act 2's rope waits for it instead)."""
import copy
from lib_s7 import *

n = load("npcs.json")
sp = n["speakers"]
for k, val in {
    "scene_gate_dawn": {"name": "The South Gate", "title": "First light", "glyph": "shield"},
    "scene_in_my_count": {"name": "The South Gate", "title": "Morning", "glyph": "shield"},
    "scene_knocking": {"name": "The South Gate", "title": "Dusk", "glyph": "moon"},
    "scene_did_he": {"name": "The Well", "title": "Morning", "glyph": "howl"},
    "scene_his_cup": {"name": "The South Gate", "title": "Dusk", "glyph": "moon"},
    "warden_answer": {"name": "The Ford-Warden", "title": "Keeper of the Low Crossing", "glyph": "skull"},
}.items():
    sp[k] = val
save("npcs.json", n)

r = load("rules.json")
for x in r["rules"]:
    if x["id"] == "nell.burial":
        x["report"] = (
            "Brannoc banked his forge at dusk yesterday and went down the Low Ford road alone, with a lantern and a "
            "blanket, between his irons. At the ford one blue light went out. He came back up the road at sunrise "
            "with the blanket in his arms, and Chid walked out past the guards to meet him, and walked beside him up "
            "the street. They are burying her this morning, behind the shrine, next to the old captain. Nobody has "
            "been asked to come.")
    if x["id"] == "nell.burial_with":
        x["report"] = (
            "Brannoc banked his forge at dusk yesterday, and you walked down the Low Ford road with him in the last of "
            "the light, between his irons. He never once looked up at them. Under the last one, over the ditch, he "
            "stopped, and reached up, and closed his bare hand round the light until it went out. He made no sound. He "
            "opened his hand. Then he got down into the ditch for her. Two small new boots stuck out of the blanket's "
            "end all the way home. They are burying her this morning, behind the shrine, next to the old captain.")
    if x["id"] == "chapter.ready":
        x["when"]["all"] = [c for c in x["when"]["all"] if c != fact("holloway.confessed", True)]
save("rules.json", r)

# The fortune's third reading: the one that mattered most in this player's game. Her bought past
# first (the fortune quoting her pillow talk is Act 1's own twist), then where the crates went,
# then Pell, and only then "Of before the ford, I see very little."
head = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dialogue_head.json"), encoding="utf-8"))
hv = head["vonnra"]["nodes"]
d = load("dialogue.json")
fp = d["vonnra"]["nodes"]["f_past"]
past = fp["text"]
sold = [x for x in past if x.get("when")]
fallback = [x for x in past if not x.get("when")]
crates = [x for x in hv["f_ember"]["text"] if x.get("when") and "knows" not in json.dumps(x["when"])]
pell = [x for x in hv["f_pell"]["text"] if x.get("when")]
fp["text"] = sold + copy.deepcopy(crates) + copy.deepcopy(pell) + fallback
save("dialogue.json", d)
print("ok", len(sold), len(crates), len(pell), len(fallback))
