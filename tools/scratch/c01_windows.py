"""The cinematics lead's windows for C01's two new lines; f_below quiet, not hushed (story lead)."""
import glob
import json
import re


def patch(lid, upd):
    hit = [p for p in sorted(glob.glob("tools/vo/direction/*.json")) if f'"{lid}"' in open(p, encoding="utf-8").read()][-1]
    t = open(hit, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', t, re.M)
    d = json.loads(m.group(1))
    d.update(upd)
    line = m.group(0)
    t = t.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(t)
    open(hit, "w", encoding="utf-8", newline="\n").write(t)


LAMP = {"time": [8.0, 9.0], "beats": "Far up the road one lamp burns high in the dark, [breath] and a voice comes down to you over "
        "the frost, close as if she stood at your shoulder.",
        "note": "Plain and quiet. A small breath at the comma before 'and a voice': the cut goes from the far lamp to her there.",
        "time_note": "a small breath at the comma before 'and a voice'"}
CALL = {"time": [3.0, 3.6], "time_note": "distant but every word clear; the outdoor tail after it is welcome"}
for lid in ("dlg.cin_drowned_fire.lamp.0", "say.e6fc0151e69a"):
    patch(lid, LAMP)
for lid in ("dlg.cin_drowned_fire.call.0", "say.bc92c07d79db"):
    patch(lid, CALL)
for lid in ("dlg.vonnra.f_below.0", "dlg.vonnra.f_below.1"):
    patch(lid, {"vol": "quiet", "pace": "very slow",
                "note": "The deepest reading: slower and lower, never whispered (a whisper turns her breathy). Unhurried images; "
                        "'they think it will be grateful' with pity. The roof shivers, and she does not finish: trails off on the "
                        "door, deliberately."})
print("ok")
