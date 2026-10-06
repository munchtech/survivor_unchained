"""The story lead's Sella notes (3 October): her own directions on her words quoted in
narration, the mornings, the sale she hides, and character-level wants and hides."""
import glob
import json
import re
from collections import OrderedDict

FILES = sorted(glob.glob("tools/vo/direction/*.json"))


def patch(lid, upd=None, fn=None):
    """Update the entry where it is defined last (the one that wins)."""
    hit = None
    for path in FILES:
        if re.search(r'^ "' + re.escape(lid) + r'": ', open(path, encoding="utf-8").read(), re.M):
            hit = path
    assert hit, lid
    text = open(hit, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
    d = json.loads(m.group(1))
    d.update(upd or {})
    if fn:
        fn(d)
    line = m.group(0)
    text = text.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(text)
    open(hit, "w", encoding="utf-8", newline="\n").write(text)


SELL = "she knows who pays for a thing like this, and unless she has stopped selling you, Vonnra will have it by noon"
patch("dlg.sella.morning.0", {
    "hides": SELL,
    "note": "The first time anyone says it (the bible's 'body's hours'). Narrator: her palm on your breastbone. 'cold as the river "
            "all night' puzzled, half a joke she doesn't quite make; 'warm as toast' a shade too bright. '...Rook's got a word for "
            "that. It's not a nice word.' quieter; not looking at you, because she's already counting it: as near as she comes to "
            "warning you. 'Get up and eat something.' brisk care, and real."})
patch("dlg.sella.morning.1", {"emo": "fond, teasing", "intent": "you're a habit",
                              "note": "Rook's complaint relayed with relish; a brisk send-off with a dark joke."})
patch("dlg.sella.rest_morning.0", {"hides": SELL, "note": "Narrator: her hand on your chest. Quiet wonder at the cold. Then warm "
      "and wry: 'Best money I ever made.' doubles (she'll be paid for it twice): play it as a joke and nothing more; the listener "
      "finds the rest."})
patch("dlg.sella.free_want.0", {"emo": "dry, then decided", "note": "Narrator: the breath. Not tears: she is never pitiful. Telling "
      "you she might cry is the most naked thing she says, and she says it dry; then she decides. 'Yes.' twice, the second "
      "firmer. 'Come here.' soft."})
patch("bark.sella.night.1", {"emo": "teasing", "vol": "quiet", "note": "An invitation dressed as thrift."})

# Her words inside the narration are hers.
Q = {
    "dlg.sella.night.1": {"emo": "low, caught", "vol": "quiet", "note": "Low. She stops you looking at her because tonight has "
                          "stopped being work and she can't have you see it; the kiss cuts it off."},
    "dlg.sella.free_night.1": {"emo": "wonder, nearly asleep", "vol": "quiet", "note": "Into your shoulder, nearly asleep. Wonder, "
                               "not tears. You told her your past knowing she sells it, and that is the whole night."},
    "dlg.sella.stairs_room.0": {"emo": "amused, and meaning it", "vol": "quiet", "note": "A professional's line that happens to be true."},
    "dlg.sella.stairs_room.1": {"emo": "dry", "vol": "quiet", "note": "A warning dressed as a joke."},
    "dlg.sella.stairs_room.2": {"emo": "teasing", "vol": "quiet", "note": "She has noticed the cold, and the joke is how she makes it nothing."},
    "dlg.sella.stairs_room.3": {"emo": "delighted", "vol": "quiet", "note": "Into your ear, delighted to make you jump."},
    "dlg.sella.free_bolt.0": {"emo": "barely voiced", "vol": "quiet", "note": "Her forehead against the door and her back to you. "
                              "She has never shot it; the word is the decision."},
    "dlg.sella.free_m_kiss.0": {"emo": "smiling", "vol": "quiet", "note": "Smiling as she pushes you off: the truth under the joke."},
}
# The stairs room's later variants say the same words.
for a, b in ((0, 4), (1, 5), (2, 6), (3, 7)):
    Q[f"dlg.sella.stairs_room.{b}"] = Q[f"dlg.sella.stairs_room.{a}"]
for lid, q in Q.items():
    patch(lid, {"quote": q})

P = "tools/vo/cast.json"
c = json.load(open(P, encoding="utf-8"), object_pairs_hook=OrderedDict)
s = c["voices"]["sella"]
s["wants"] = ("a house in the south with a door that locks from the inside, and somebody who knocks; until then, your custom, "
              "and to keep it work")
s["hides"] = ("she sells what's said upstairs, and Vonnra outbids everyone: every intimate scene has a buyer listening, until she "
              "stops (sella.free). Adult, frank, never breathy, never coy")
open(P, "w", encoding="utf-8", newline="\n").write(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
print("ok")
