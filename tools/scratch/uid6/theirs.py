"""Resolve every conflict block in a file by taking the incoming side (theirs)."""
import re
import sys

p = sys.argv[1]
s = open(p, encoding='utf-8', newline='').read()
pat = re.compile(r'<<<<<<< [^\n]*\n(.*?)=======\r?\n(.*?)>>>>>>> [^\n]*\n', re.S)
s, n = pat.subn(lambda m: m.group(2), s)
open(p, 'w', encoding='utf-8', newline='').write(s)
print(p, n, 'blocks')
