"""Exact substitutions in a file, keeping its line endings: sub.py FILE SUBS.py
SUBS.py defines PAIRS = [(old, new), ...]; each old must occur exactly once."""
import sys, runpy
p = sys.argv[1]
pairs = runpy.run_path(sys.argv[2])['PAIRS']
s = open(p, encoding='utf-8', newline='').read()
crlf = '\r\n' in s
for a, b in pairs:
    if crlf:
        a = a.replace('\r\n', '\n').replace('\n', '\r\n')
        b = b.replace('\r\n', '\n').replace('\n', '\r\n')
    n = s.count(a)
    if n != 1:
        sys.exit(f'{n} matches for: {a[:100]!r}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='').write(s)
print(f'ok: {len(pairs)} substitutions')
