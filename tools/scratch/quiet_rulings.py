"""The story lead's rulings: quiet, not a whisper (Maeca's counted morning, Redcowl's last words)."""
import glob
import json
import re


def patch(lid, upd):
    hit = [p for p in sorted(glob.glob("tools/vo/direction/*.json")) if re.search(r'^ "' + re.escape(lid) + r'": ', open(p, encoding="utf-8").read(), re.M)][-1]
    t = open(hit, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', t, re.M)
    d = json.loads(m.group(1))
    d.update(upd)
    line = m.group(0)
    t = t.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(t)
    open(hit, "w", encoding="utf-8", newline="\n").write(t)
    print("patched", lid)


patch("dlg.maeca.blind3_morning.0", {"vol": "quiet", "note": "Quiet, low, level and close, never whispered: a hunter's report "
      "on what she counted ('I counted between'), frightened under it. A whisper would make it a lover's line, and it is a "
      "hunter's. The narrator's parts stay plain."})
patch("dlg.cin_raid_on_the_roost.last.1", {"vol": "quiet", "note": "Quiet, on the last of the breath, never whispered: it is "
      "still an order to his men about his brother. A whisper would make it a stage death; let the breath be in the pauses."})
patch("dlg.cin_raid_on_the_roost.last.0", {"note": "The laugh is real, and there is no whisper: quiet, on what breath he has."})
