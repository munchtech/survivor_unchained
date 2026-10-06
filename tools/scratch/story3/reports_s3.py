"""Add the morning reports for the story nights to rules.json (round-trip format: indent 1,
ensure_ascii False, CRLF, trailing CRLF), after dig.burned. Checks the round trip first."""
import json, sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot\data\content\rules.json"
raw = open(p, "rb").read()
data = json.loads(raw.decode("utf-8"))
def dump(d):
    return (json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8")
if dump(data) != raw:
    sys.exit("round trip differs; not writing")
new = [
    {"id": "hollow.killed", "once": True, "when": {"history": "killed_greymuzzle"}, "effect": [],
     "report": "Just before dawn the Pack howled from the Hollow, all of them together, once, and not again. Maeca was through the east gate the moment it opened, and did not say where she was going. Nobody asked."},
    {"id": "hollow.spared", "once": True, "when": {"history": "spared_greymuzzle"}, "effect": [],
     "report": "Tam says he saw an old grey wolf on the ridge at first light, walking slow, and it stood and looked at the town for a long time before it went. Nobody believes him."},
    {"id": "roost.cairn", "once": True, "when": {"history": "killed_redcowl"}, "effect": [],
     "report": "Lamps moved in the ravine all night. At first light there was a cairn at the top of the Roost road, where the Old Road can see it. The Flagon's back room stayed shut all morning, and nobody saw Rav go out."},
    {"id": "dig.quiet", "once": True, "when": {"all": [{"history": "broke_dig"}, {"not": {"fact": "dig.pump", "eq": "blown"}}]}, "effect": [],
     "report": "The hill over the Dig stayed dark after you came down from it. At first light Snib was sitting on an upturned bucket at the pit mouth, with his chin in his hands, waiting for somebody to tell him what to do."},
    {"id": "vault.watched", "once": True, "when": {"history": "opened_vault"}, "effect": [],
     "report": "Vonnra came down from the toll tower before dawn, which nobody has seen her do, and walked out along the Verge road and back. She paid the gate-guard for his trouble, and told him he had not seen her."},
]
rules = data["rules"]
ids = [r["id"] for r in rules]
for r in new:
    if r["id"] in ids:
        sys.exit(f"{r['id']} already there")
at = ids.index("dig.burned") + 1
data["rules"] = rules[:at] + new + rules[at:]
open(p, "wb").write(dump(data))
print("added", len(new), "after dig.burned")
