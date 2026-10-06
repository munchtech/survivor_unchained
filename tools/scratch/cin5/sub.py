"""Exact substitutions in a file, keeping its line endings: python sub.py FILE EDITS.py
EDITS.py defines R = [(old, new), ...]; each old must occur exactly once."""
import importlib.util
import sys

p, e = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("e", e)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
for old, new in m.R:
    if crlf:
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    n = t.count(old)
    if n != 1:
        sys.exit(f"{n} matches for: {old[:90]!r}")
    t = t.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok", len(m.R))
