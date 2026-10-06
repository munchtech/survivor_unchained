"""combine.py <out faces.json> [--bare] name=fit.json ... : one faces file from fits (bare: without FACE under them)."""
import json
import sys

out = {}
bare = "--bare" in sys.argv
for a in sys.argv[2:]:
    if a == "--bare":
        continue
    name, path = a.split("=", 1)
    w = json.load(open(path, encoding="utf-8-sig"))
    if bare:
        w["-"] = True
    out[name] = w
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(len(out), "faces")
