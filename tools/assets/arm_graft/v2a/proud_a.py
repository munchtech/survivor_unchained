# Body 2 A: d_c m.run + a.py (deltoid proud/V, triceps, sections) with "graft" = the given glb.  run in body2/d_c
import sys, os, pickle
sys.path.insert(0, ".")
import m
glb = sys.argv[1]; m.BODIES["graft"] = glb
res = m.run(); [res[k].pop("b") for k in res]
pk = os.path.join(os.path.dirname(glb), "res.pkl"); pickle.dump(res, open(pk, "wb"))
src = open("a.py").read().replace('pickle.load(open(B + r"\d_c\res.pkl", "rb"))', "pickle.load(open(%r, 'rb'))" % pk)
assert "%r" % pk in src or pk in src
exec(compile(src, "a", "exec"))
