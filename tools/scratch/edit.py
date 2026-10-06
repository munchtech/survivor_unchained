"""Apply exact, unique replacements to a file: python edit.py FILE PAIRS.py
PAIRS.py defines PAIRS = [(old, new), ...]."""
import sys, runpy
path, pairs_file = sys.argv[1], sys.argv[2]
pairs = runpy.run_path(pairs_file)["PAIRS"]
s = open(path, encoding="utf-8").read()
for a, b in pairs:
    n = s.count(a)
    if n != 1:
        print(f"NOT UNIQUE ({n}) in {path}: {a[:90]!r}")
        sys.exit(1)
    s = s.replace(a, b)
open(path, "w", encoding="utf-8", newline="").write(s)
print("ok", path, len(pairs))
