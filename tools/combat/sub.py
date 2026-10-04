"""Exact, unique replacements in a file, keeping its line endings.
usage: python tools/combat/sub.py SPEC.py   where SPEC.py defines FILES = {path: [(old, new), ...]}"""
import sys, runpy

spec = runpy.run_path(sys.argv[1])
for path, pairs in spec["FILES"].items():
    raw = open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            sys.exit(f"{path}: {n} matches for {old[:70]!r}")
        s = s.replace(old, new)
    if crlf:
        s = s.replace("\n", "\r\n")
    open(path, "w", encoding="utf-8", newline="").write(s)
    print(f"{path}: {len(pairs)} done")
