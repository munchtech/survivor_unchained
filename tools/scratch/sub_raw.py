"""Exact substitutions with no line-ending conversion: sub_raw.py FILE SUBS.py"""
import sys, runpy
p = sys.argv[1]
pairs = runpy.run_path(sys.argv[2])['PAIRS']
s = open(p, encoding='utf-8', newline='').read()
for a, b in pairs:
    n = s.count(a)
    if n != 1:
        sys.exit(f'{n} matches for: {a[:100]!r}')
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='').write(s)
print(f'ok: {len(pairs)} substitutions')
