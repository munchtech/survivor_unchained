# Runs heroine_outfits.py up to its export loop and lists each outfit's built pieces (name, material, hides).
import os, sys, json
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "heroine_outfits.py")
P = os.path.abspath(P)
src = open(P, encoding="utf-8").read()
key = 'pieces_of = {name: [o for o in made if o.name.startswith(name + ".")] for name in OUTFITS}'
assert src.count(key) == 1
src = src.replace(key, key + '\nimport json as _j\n_rows = [[o.name, o.data.materials[0].name if o.data.materials else "none", bool(o.get("hides")), len(o.data.vertices)] for o in made]\nopen(os.environ["LIST_OUT"], "w").write(_j.dumps(_rows, indent=0))\nprint("LISTED", len(_rows))\nimport sys as _s; _s.exit(0)\n')
g = {"__file__": P, "__name__": "__main__"}
exec(compile(src, P, "exec"), g)
