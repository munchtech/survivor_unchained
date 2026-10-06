"""The fortune gives the first chart (f_door split: the door, then f_chart, priced and waived), and the
fortune's crates follow a spared Redcowl over the ridge."""
import sys
sys.path.insert(0, r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\story5")
from jsonio_s5 import load, save

d = load("dialogue.json")
v = d["vonnra"]["nodes"]
if "f_chart" in v: sys.exit("already applied")
door = v["f_door"]
acc = {"fact": "vonnra.accused", "eq": True}
assert door["text"][0]["text"].endswith("That is all I see for free, {name}. The rest you will walk into yourself, and you will, because you are the kind that does.")
door["text"] = [
    {"when": acc, "text": "The door in the hillside is listening, as I am. That is all I see for free, {name}."},
    {"text": "The door is not for sale. That is all I see for free."},
]
choices = door.pop("choices")
door["next"] = "f_chart"
lay = "(She takes a folded chart from under the ledger and lays it between you. It is the Wayfinder's, and the margins are full.) "
rest = " The rest you will walk into yourself, and you will, because you are the kind that does."
v["f_chart"] = {
    "id": "f_chart",
    "text": [
        # Accused, she has said the name once already; the chart is neither "traveller" nor the name.
        {"when": acc, "text": lay + "That would be ten gold. This once, no charge." + rest},
        {"text": lay + "That would be ten gold, traveller. This once, no charge." + rest},
    ],
    "effects": [{"chart": {"people": "dead", "tier": 1, "rarity": 0, "name": "The Lampless Howes"}}],
    "choices": choices,
}
# Keep the node order readable: f_chart straight after f_door.
nodes = list(v.items())
i = [k for k, _ in nodes].index("f_door") + 1
nodes = [(k, n) for k, n in nodes if k != "f_chart"]
nodes.insert(i, ("f_chart", v["f_chart"]))
d["vonnra"]["nodes"] = dict(nodes)

# The fortune's crates: spared, he took them over the ridge.
emb = d["vonnra"]["nodes"]["f_ember"]["text"]
assert emb[0]["when"] == {"fact": "be.crates", "eq": "redcowl"}
emb.insert(0, {"when": {"all": [{"fact": "be.crates", "eq": "redcowl"}, {"fact": "redcowl", "eq": "spared"}]},
               "text": "And six crates on a cart going north over the ridge, and a man walking behind it who knows what they are for. He will not sell them. He is saving them. I wonder for what."})
save("dialogue.json", d)
print("applied")
