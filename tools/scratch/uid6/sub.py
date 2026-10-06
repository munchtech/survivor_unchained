"""Replace text in a file keeping its line endings: python sub.py FILE PAIRS.py
PAIRS.py defines PAIRS = [(old, new), ...] written with \n; each old must be found exactly once."""
import runpy
import sys

p = sys.argv[1]
pairs = runpy.run_path(sys.argv[2])['PAIRS']
s = open(p, encoding='utf-8', newline='').read()
crlf = '\r\n' in s
for old, new in pairs:
    if crlf:
        old, new = old.replace('\n', '\r\n'), new.replace('\n', '\r\n')
    n = s.count(old)
    if n != 1:
        sys.exit(f'{p}: found {n} times: {old[:80]!r}')
    s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='').write(s)
print(p, len(pairs), 'replaced')
