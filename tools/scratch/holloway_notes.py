"""The story lead's five direction notes on Holloway (3 October): no line changes."""
import json
import re
from collections import OrderedDict

# 1. Character-level wants and hides.
P = "tools/vo/cast.json"
c = json.load(open(P, encoding="utf-8"), object_pairs_hook=OrderedDict)
h = c["voices"]["holloway"]
h["wants"] = "to keep the town alive on eleven men and a year without pay, and to be left to count it"
h["hides"] = ("he signed for the Ashford garrison's boots, and the boots never came; Maeca's bare feet are his doing, as he sees it. "
              "Later, the letter under his cup is from the north, asking for \"the one from the ford\", which means you; every time "
              "he looks at you after that, he is deciding whether to answer it")
open(P, "w", encoding="utf-8", newline="\n").write(json.dumps(c, indent=1, ensure_ascii=False) + "\n")


def patch(path, lid, upd):
    text = open(path, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
    assert m, lid
    d = json.loads(m.group(1))
    d.update(upd)
    for k in [k for k, v in upd.items() if v is None]:
        d.pop(k, None)
    line = m.group(0)
    text = text.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(text)
    open(path, "w", encoding="utf-8", newline="\n").write(text)


H = "tools/vo/direction/holloway.json"
# 2. The letter is about the person he is speaking to.
patch(H, "dlg.holloway.letter.0", {
    "hides": "the letter is about you: the north asks for \"the one from the ford\"",
    "note": "'Mine.' hard. Narrator: the cup doesn't move. 'Read your own post, if anybody writes to you.' is curt cover; "
            "he looks at you a beat too long before it."})
# 3. Aldo: no crack; paying is the nearest he gets to sorry.
patch(H, "dlg.holloway.hub.1", {
    "note": "Quartermaster's list for a dead man. 'by the bad leg' barely steady. No crack: 'I'd give a month's pay to hear him "
            "hum.' is the grief itself (paying is the nearest he gets to sorry), flatter and slower than the rest. Then straight "
            "back to business: 'Five a pelt, still. What do you want?'"})
# 4. He does not shout at a person.
patch(H, "dlg.holloway.defied.0", {
    "emo": "cold", "vol": "level",
    "note": "His anger stays one notch below the surface; he doesn't shout at a person. 'Out of my sight.' sharp but level. "
            "The threat about the cell-rats almost pleasant."})
# 5. The second "One." was cut.
patch("tools/vo/direction/story2.json", "bark.holloway.said.3", {"note": "'One caravan' weighed; 'I'll take it.' accepting."})
print("ok")
