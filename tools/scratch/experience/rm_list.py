"""Delete the generated files a merge says are in its way: python rm_list.py LIST ROOT
(only .uid and .import files, which imports regenerate)."""
import os, sys

lst, root = sys.argv[1], sys.argv[2]
n = 0
for line in open(lst, encoding="utf-8"):
    p = line.strip()
    if not p or not (p.endswith(".uid") or p.endswith(".import")):
        continue
    f = os.path.join(root, p)
    if os.path.isfile(f):
        os.remove(f)
        n += 1
print("removed", n)
