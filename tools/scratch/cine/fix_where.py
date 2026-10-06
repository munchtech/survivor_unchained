import json, re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
out = []
# Only inside a cue line (a line that has "do":), a place given as "at" becomes "where".
for line in s.split("\n"):
    if '"do":' in line:
        line = re.sub(r'"at": (\[|\{ "mark"|\{ "abs")', r'"where": \1', line)
    out.append(line)
s = "\n".join(out)
d = json.loads(s)
for sh in d["shots"]:
    for c in sh.get("cues", []):
        if "at" in c and not isinstance(c["at"], (int, float, str)):
            print("bad", sh["id"], c)
open(p, "w", encoding="utf-8").write(s)
print("ok")
