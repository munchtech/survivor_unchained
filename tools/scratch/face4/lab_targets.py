"""lab_targets.py out.json t1 t2 ...: faces.json with each target at +1 (and 'base'), over her FACE."""
import json
import sys

out = {"base": {}}
for t in sys.argv[2:]:
    name, _, w = t.partition("=")
    out[name] = {name: float(w or 1.0)}
json.dump(out, open(sys.argv[1], "w"), indent=1)
