import json
import sys

base = json.load(open(sys.argv[1], encoding="utf-8-sig"))
out = {}
for k in (0, 0.5, 1.0, 1.5):
    f = dict(base, **{"-": True})
    if k:
        f["sculpt-chin-narrow"] = k
    out[f"chin{int(k * 10):02d}"] = f
f = dict(base, **{"-": True})
f["chin-width-decr"] = f.get("chin-width-decr", 0) + 1.5
f["sculpt-chin-narrow"] = 1.0
out["chin10w"] = f
json.dump(out, open(sys.argv[2], "w"), indent=0)
