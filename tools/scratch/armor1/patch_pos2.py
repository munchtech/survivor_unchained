import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
a = '''    assert np.allclose(np.array(body_obj.matrix_world), np.eye(4), atol=1e-9), "her body is not at the origin"
    bp = np.empty(len(me_.vertices) * 3, np.float32)
    me_.vertices.foreach_get("co", bp)
    bp = bp.reshape(-1, 3)'''.replace("\n", "\r\n")
b = '''    bp = np.empty(len(me_.vertices) * 3, np.float32)
    me_.vertices.foreach_get("co", bp)
    bp = bp.reshape(-1, 3)
    if not np.allclose(np.array(body_obj.matrix_world), np.eye(4), atol=1e-9):
        print("ARMOR TUCK: her body is not at the origin; its points taken through its matrix")
        bp = np.array([(body_obj.matrix_world @ v.co)[:] for v in me_.vertices], np.float32)'''.replace("\n", "\r\n")
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
