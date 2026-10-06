"""Sella's mornings moved down one when the 'cold as the river' morning was put first:
each direction back on its own words, and one for the new morning."""
import json
import re

P = "tools/vo/direction/sella.json"
text = open(P, encoding="utf-8").read()


def entry(lid):
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
    return m, json.loads(m.group(1))


m0, d0 = entry("dlg.sella.morning.0")
m1, d1 = entry("dlg.sella.morning.1")
assert d0["intent"] == "you're a habit" and "Not badly" in d1["note"]
new0 = {"emo": "fond, uneasy under it", "intent": "she noticed the body's hours", "pace": "measured", "vol": "quiet",
        "hides": "Rook's word frightens her",
        "note": "The first time anyone says it (the bible's 'body's hours'). Narrator: her palm on your breastbone. 'cold as the "
                "river all night' puzzled, half a joke she doesn't quite make; 'warm as toast' a shade too bright. '...Rook's got a "
                "word for that. It's not a nice word.' quieter, uneasy, not looking at you. Then brisk care to cover it: 'Get up "
                "and eat something.'"}
text = text.replace(m0.group(0), ' "dlg.sella.morning.0": ' + json.dumps(new0, ensure_ascii=False) + ("," if m0.group(0).endswith(",") else ""))
# The habit morning is now .1; the note on .1 ('Not badly') belongs to .3, which has its own direction (imported.json).
text = text.replace(m1.group(0), ' "dlg.sella.morning.1": ' + json.dumps(d0, ensure_ascii=False) + ("," if m1.group(0).endswith(",") else ""))
json.loads(text)
open(P, "w", encoding="utf-8", newline="\n").write(text)
print("ok")
