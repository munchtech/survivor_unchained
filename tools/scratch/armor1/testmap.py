import json, re, sys, collections
m = json.load(open("tools/armor/slot_map.json"))
rows = json.load(open(sys.argv[1]))
bad = []; by = collections.defaultdict(lambda: collections.defaultdict(list))
for n, *_ in rows:
    o, p = n.split(".", 1)
    hit = [e["slot"] for e in m["outfits"][o] if any(re.fullmatch(r, p) for r in e["match"])]
    if len(hit) != 1: bad.append((n, hit))
    else: by[o][hit[0]].append(p)
print("bad", bad)
for o, d in by.items():
    for s, l in d.items(): print(o, s, len(l), " ".join(x for x in l if not re.search(r"_(bind|stitch|trim|rivets|gold|lining)\d*$|weltstitch", x)))
