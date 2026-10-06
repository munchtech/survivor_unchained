"""The story lead's sign-off: narrator and Rook final, Rook's valley hides, the Red Hand cast on paper, '+' read as 'and'."""
import json
import os
import re

# Rook's valley.0: the canon hides.
D = "tools/vo/direction"
for f in os.listdir(D):
    if not f.endswith(".json"):
        continue
    p = os.path.join(D, f)
    d = json.load(open(p, encoding="utf-8"))
    if "dlg.rook.valley.0" in d:
        d["dlg.rook.valley.0"]["hides"] = ("she knows who stood on which side of it, and that it isn't over "
                                            "(the Kerchiefs are what's left of Ashford)")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in d.items()) + "\n}\n")

# The Red Hand: a Kerchief enforcer, cast cheaply (story lead).
c = json.load(open("tools/vo/cast.json", encoding="utf-8"))
c["voices"]["red_hand"] = {
    "name": "The Red Hand", "sex": "m", "age": 45, "accent": "hard west-of-Scotland Scots",
    "design": "A Kerchief enforcer in his forties, one of Ashford's old levy, with a low, flat, hard west-of-Scotland voice. "
              "He never raises it: he is collecting a debt, not threatening. Few words to strangers, and those flat.",
    "ref_text": "Toll's due. Same as last month, and the month before. Put it in the hand and walk on.",
    "room": "outdoor", "tempo": [2.2, 3.0],
    "maya": "Realistic male voice in the 40s age with scottish accent, a debt collector. Low pitch, flat hard timbre, slow pacing, flat tone.",
}
with open("tools/vo/cast.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump(c, fh, indent=1, ensure_ascii=False)
    fh.write("\n")

p = "tools/vo/lines.py"
t = open(p, encoding="utf-8").read()
t = t.replace('"The Barrow Lord": "barrow_lord"}', '"The Barrow Lord": "barrow_lord", "The Red Hand": "red_hand"}')
open(p, "w", encoding="utf-8", newline="\n").write(t)

# Packets the story lead has marked final.
p = "tools/vo/elevenlabs.py"
t = open(p, encoding="utf-8").read()
if "FINAL = " not in t:
    t = t.replace("HOLD_VOICES: dict = {}", "HOLD_VOICES: dict = {}\n# Packets the story lead has checked and marked final (voice: date).\nFINAL = {\"narrator\": \"2026-10-03\", \"rook\": \"2026-10-03\"}")
    t = t.replace('''tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.", ""]''',
                  '''tries a line). " + (f"Status: **final** (the story lead, {FINAL[voice]}): record it." if voice in FINAL else
                                    "Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final."), ""]''')
    assert "FINAL[voice]" in t
open(p, "w", encoding="utf-8", newline="\n").write(t)

# The importer reads a carved "+" as "and" (the well's "M. + J.").
p = "tools/vo/import_takes.py"
t = open(p, encoding="utf-8").read()
t = t.replace('''            rep = ears.hear(tmp, m["text"], m["voice"])''', '''            rep = ears.hear(tmp, re.sub(r"\\s\\+\\s", " and ", m["text"]), m["voice"])''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("ok")
