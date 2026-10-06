"""Apply exact, unique replacements across files: python multi.py SPEC.py (SPEC defines FILES = {path: [(old, new), ...]})."""
import sys, runpy
files = runpy.run_path(sys.argv[1])["FILES"]
staged = {}
for path, pairs in files.items():
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        n = s.count(a)
        if n != 1:
            print(f"NOT UNIQUE ({n}) in {path}: {a[:90]!r}")
            sys.exit(1)
        s = s.replace(a, b)
    staged[path] = s
for path, s in staged.items():
    open(path, "w", encoding="utf-8", newline="").write(s)
    print("ok", path)
