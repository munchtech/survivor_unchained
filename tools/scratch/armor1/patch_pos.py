import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
a = '''    bp = np.array([(body_obj.matrix_world @ v.co)[:] for v in me_.vertices])
    q = np.round(np.stack([bp[:, 0], bp[:, 2], -bp[:, 1]], 1) * 1e5).astype(np.int64)'''.replace("\n", "\r\n")
b = '''    # (her points as the exporter writes them, float32 in her mesh's own frame (her world frame: asserted), so
    # each rounds as the game's copy of them does)
    assert np.allclose(np.array(body_obj.matrix_world), np.eye(4), atol=1e-9), "her body is not at the origin"
    bp = np.empty(len(me_.vertices) * 3, np.float32)
    me_.vertices.foreach_get("co", bp)
    bp = bp.reshape(-1, 3)
    q = np.round(np.stack([bp[:, 0], bp[:, 2], -bp[:, 1]], 1).astype(np.float64) * 1e5).astype(np.int64)'''.replace("\n", "\r\n")
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
