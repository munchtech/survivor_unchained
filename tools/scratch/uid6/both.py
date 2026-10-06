"""Resolve conflict blocks by keeping ours, then theirs, with a replacement for lines both sides
declare: python both.py FILE 'old line=>new line' ..."""
import re
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8', newline='').read()
pat = re.compile(r'<<<<<<< [^\n]*\n(.*?)=======\r?\n(.*?)>>>>>>> [^\n]*\n', re.S)
s, n = pat.subn(lambda m: m.group(1) + m.group(2), s)
for rule in sys.argv[2:]:
    old, new = rule.split('=>')
    s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='').write(s)
print(p, n, 'blocks')
