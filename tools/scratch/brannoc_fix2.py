"""nell_ditch.1: the note in the order things happen; the stale beats (the narrator no longer cuts in) dropped."""
import json
import re

P = "tools/vo/direction/brannoc.json"
lid = "dlg.brannoc.nell_ditch.1"
text = open(P, encoding="utf-8").read()
m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
d = json.loads(m.group(1))
d["note"] = ("He does not break. The narrator only puts the hammer down. 'Had the reins.' barely voiced. The long breath through "
             "the nose is his, between 'Had the reins.' and 'She'd want the reins.' Flat facts about his daughter; the love is only "
             "in saying 'the reins' again.")
d.pop("beats", None)
line = m.group(0)
text = text.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
json.loads(text)
open(P, "w", encoding="utf-8", newline="\n").write(text)
print("ok")
