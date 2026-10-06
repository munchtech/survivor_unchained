"""The story lead's five direction fixes on Brannoc (3 October): no line changes."""
import json
import re
from collections import OrderedDict


def patch(path, lid, upd=None, fn=None):
    text = open(path, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
    assert m, lid
    d = json.loads(m.group(1))
    if upd:
        d.update(upd)
    if fn:
        fn(d)
    line = m.group(0)
    text = text.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(text)
    open(path, "w", encoding="utf-8", newline="\n").write(text)


B = "tools/vo/direction/brannoc.json"


def ditch(d):
    old = "Narrator: the long breath (so none in his read)."
    assert old in d["note"], d["note"]
    d["note"] = d["note"].replace(old, "The narrator only puts the hammer down. The long breath through the nose is his, between "
                                       "'Had the reins.' and 'She'd want the reins.'")
    d["note"] = d["note"].replace("Narrator: the hammer goes down, which you have never seen. ", "")


patch(B, "dlg.brannoc.nell_ditch.1", fn=ditch)
patch("tools/vo/direction/story2.json", "bark.brannoc.said.1",
      {"note": "Once only. Barely voiced, to the iron, not to her: twelve irons, and a girl of twelve he made."})
# A whispered bass loses him: quiet and low, the voice nearly going.
patch(B, "dlg.brannoc.nell_quick.0", {"vol": "quiet", "note": "The only thanks he gives in the game, and it must sound like him: "
      "no whisper. Narrator holds the long time. '...Thank you.' quiet and low, deep, the voice nearly going. Narrator: the forge "
      "cools. 'Forge is shut. Go on.' quiet."})
patch("tools/vo/direction/additions.json", "dlg.cin_road_back.wat.0", {"vol": "quiet", "note": "Quiet and low, the voice nearly "
      "going; no whisper (a whispered bass loses him)."})

P = "tools/vo/cast.json"
c = json.load(open(P, encoding="utf-8"), object_pairs_hook=OrderedDict)
b = c["voices"]["brannoc"]
b["design"] = b["design"].replace("with a rolled 'r'", "with a burred West Country 'r'")
assert "burred" in b["design"]
b["wants"] = "before the truth, to work, and his girl safe at her aunt's in Low Kiln"
b["hides"] = ("before the truth, the fear he won't name: he has been stopping every carter on the south road to ask, which is why "
              "his one question comes out with too many words. After the truth (C08) he hides nothing: each line in that stretch "
              "is a man holding a weight he made himself; the irons were his")
open(P, "w", encoding="utf-8", newline="\n").write(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
print("ok")
