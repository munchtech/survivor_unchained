"""C01's voice up the road (the story lead, ae194ff): the narrator's lamp line and Vonnra's call,
each also a prologue caption with the same words; and the fortune's 'No charge, this once.' as its twin."""
import glob
import hashlib
import json
import re


def h(t):
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]


LAMP = "Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder."
CALL = "Come up, traveller. ...No charge, this once."
lamp = {"emo": "plain", "intent": "a lamp, and a voice up the road", "pace": "slow", "vol": "quiet", "note": "Plain and quiet; no pause needed."}
call = {"emo": "kindly, unhurried", "intent": "a toll-keeper waving a traveller through", "pace": "slow", "vol": "quiet",
        "wants": "the risen traveller up the road and into her town before dawn", "hides": "that she made them",
        "note": "Far off and thinned by the cold, never raised; the frost carries it, close as if at the shoulder. The pause before "
                "'No charge' is her deciding to. The game adds the distance (the 'far' effect): record it dry and close.",
        "beats": "Come up, traveller. [beat] ...No charge, this once.", "fx": "far", "room": "close"}
NEW = {"dlg.cin_drowned_fire.lamp.0": lamp, f"say.{h(LAMP)}": lamp, "dlg.cin_drowned_fire.call.0": call, f"say.{h(CALL)}": call}

P = "tools/vo/direction/additions.json"
text = open(P, encoding="utf-8").read().rstrip()
assert text.endswith("}")
body = text[:-1].rstrip()
for k, v in NEW.items():
    if f'"{k}"' not in body:
        body += ",\n " + json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False)
text = body + "\n}\n"
json.loads(text)
open(P, "w", encoding="utf-8", newline="\n").write(text)

TWIN = " 'No charge, this once.' is the call's twin (C01): the same phrasing, close and quiet across a table, so a listener can find it."
for lid in ("dlg.vonnra.fortune.0", "dlg.vonnra.fortune.1", "dlg.vonnra.fortune.2"):
    hit = [p for p in sorted(glob.glob("tools/vo/direction/*.json")) if f'"{lid}"' in open(p, encoding="utf-8").read()][-1]
    t = open(hit, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', t, re.M)
    d = json.loads(m.group(1))
    if "call's twin" not in d.get("note", ""):
        d["note"] = (d.get("note", "") + TWIN).strip()
    line = m.group(0)
    t = t.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(t)
    open(hit, "w", encoding="utf-8", newline="\n").write(t)
print("ok", list(NEW))
