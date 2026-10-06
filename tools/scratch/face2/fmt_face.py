"""Print a face dict as face_shapes.FACE source, grouped by region and wrapped."""
import json
import sys

c = json.load(open(sys.argv[1], encoding="utf-8-sig"))
c.pop("-", None)
for a in sys.argv[2:]:
    k, v = a.split("=")
    c[k] = float(v)
order = ["head", "forehead", "eyebrows", "X-eye", "nose", "X-cheek", "mouth", "chin", "sculpt", ""]
keys = sorted(c, key=lambda k: (next(i for i, o in enumerate(order) if k.startswith(o)), k))
items = ['"%s": %s' % (k, round(c[k], 3)) for k in keys]
parts, line = [], ""
for x in items:
    if len(line) + len(x) + 2 > 116:
        parts.append(line.rstrip())
        line = ""
    line += x + ", "
parts.append(line.rstrip().rstrip(","))
print("FACE = {" + "\n        ".join(parts) + "}")
