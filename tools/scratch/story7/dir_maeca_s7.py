"""Maeca's direction notes: no "Barefoot"; the cut nodes' entries dropped; notes for her new lines.
Keeps the file's own one-entry-per-line layout."""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1\tools\vo\direction\maeca.json"
raw = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
d = json.loads(raw)
for k in [k for k in d if k.startswith("dlg.maeca.barefoot.") or k.startswith("dlg.maeca.signed.")]:
    del d[k]
for k, v in d.items():
    for f in ("note", "hides", "intent", "wants"):
        if isinstance(v.get(f), str) and "arefoot" in v[f]:
            v[f] = (v[f].replace("Maeca. Barefoot, before you ask.", "Maeca. I track for the Watch, before you ask. Not wolves.")
                        .replace("'Barefoot, before you ask'", "'I track for the Watch, before you ask'")
                        .replace("Barefoot, before you ask", "I track for the Watch, before you ask")
                        .replace("Maeca Barefoot", "Maeca"))
            print(k, f, "->", v[f][:160])
d["dlg.maeca.watch.0"] = {"emo": "flat, a little proud", "intent": "says who pays her", "pace": "measured", "vol": "quiet",
                          "wants": "nothing from you", "hides": "every week she takes his money and buys his drink with it, and she is waiting",
                          "note": "Plain. 'I take it. Every week.' a fact, not a confession. 'I don't let him.' the only warmth, and it is not warmth."}
d["dlg.maeca.ashford.0"] = {"emo": "nothing", "intent": "closes the subject", "pace": "slow", "vol": "quiet",
                            "wants": "the subject shut", "hides": "she was on the ladder, the next hand up, number ninety-two",
                            "note": "Three words, to the cup. No weight on any of them. It is her post, and his report's lie."}
left = [k for k, v in d.items() if "arefoot" in json.dumps(v)]
print("still:", left)
out = "{" + nl + ("," + nl).join(f" {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in d.items()) + nl + "}" + nl
open(P, "w", encoding="utf-8", newline="").write(out)
