import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
a = '''    q = np.round(np.stack([bp[:, 0], bp[:, 2], -bp[:, 1]], 1).astype(np.float64) * 1e5).astype(np.int64)
    uq, inv = np.unique(q, axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()'''.replace("\n", "\r\n")
b = '''    q = np.round(np.stack([bp[:, 0], bp[:, 2], -bp[:, 1]], 1).astype(np.float64) * 1e5).astype(np.int64)
    # (only her points on a face: the exporter writes no others)
    fv = np.empty(sum(len(f_.vertices) for f_ in me_.polygons), np.int64)
    me_.polygons.foreach_get("vertices", fv)
    used = np.zeros(len(me_.vertices), bool)
    used[fv] = True
    uq, inv = np.unique(q[used], axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    print("ARMOR TUCK: %d of her %d points on faces, %d places" % (int(used.sum()), len(used), len(uq)))'''.replace("\n", "\r\n")
assert s.count(a) == 1
s = s.replace(a, b)
a2 = '''        np.maximum.at(g, inv, t)'''.replace("\n", "\r\n")
assert s.count(a2) == 1
s = s.replace(a2, '''        np.maximum.at(g, inv, t[used])''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
