import json, sys, collections
rows = json.load(open(sys.argv[1]))
by = collections.defaultdict(list)
for n, m, h, nv in rows:
    o, p = n.split(".", 1)
    by[o].append("%s[%s%s]" % (p, m, "*" if h else ""))
for o, l in by.items():
    print(o, len(l)); print("  " + " ".join(l))
