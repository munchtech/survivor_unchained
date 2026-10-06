"""Vonnra's directions back on their own words: the fortune's crate variants moved when two
were added (a stream, the south road), and two notes quoted words since rewritten."""
import json
import re

P = "tools/vo/direction/vonnra.json"
text = open(P, encoding="utf-8").read()


def get(lid):
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
    return m, json.loads(m.group(1))


def put(lid, d):
    global text
    m, _ = get(lid)
    line = m.group(0)
    text = text.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))


_, burned = get("dlg.vonnra.f_ember.2")
assert burned["intent"] == "the crates burned"
put("dlg.vonnra.f_ember.2", {"emo": "cold approval", "intent": "the crates drowned", "pace": "slow", "vol": "quiet",
                             "note": "'where nothing will ever buy them' plain. 'That is the first thing you have thrown away that I "
                                     "approve of.' cold, and as near to a compliment as she comes."})
put("dlg.vonnra.f_ember.3", burned)  # the Roost: 'Everyone did.'
put("dlg.vonnra.f_ember.4", {"emo": "dry, knowing", "intent": "the crates sold on", "pace": "slow", "vol": "quiet",
                             "note": "'sold to whoever paid for them first' flat. 'I think you know who that was.' quiet: she does, "
                                     "and so do you."})
_, fled = get("dlg.vonnra.f_pell.3")
fled["note"] = "'He took his books with him.' plain. 'You are in them.' quiet: the warning is in the last four words."
put("dlg.vonnra.f_pell.3", fled)
_, vault = get("dlg.vonnra.cb_vault3.0")
vault["note"] = "'Yours, for now.' cool. Then quiet menace. 'You will find I collect.' softly."
put("dlg.vonnra.cb_vault3.0", vault)
json.loads(text)
open(P, "w", encoding="utf-8", newline="\n").write(text)
print("ok")
