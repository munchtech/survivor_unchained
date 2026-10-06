"""splice.py <file> <start marker> <end marker (kept)> <snippet file>: the text from the start marker up to the end marker replaced."""
import sys
p, a, b, snip = sys.argv[1:5]
s = open(p, encoding="utf-8").read()
i, j = s.index(a), s.index(b)
assert i < j, (i, j)
s = s[:i] + open(snip, encoding="utf-8").read() + s[j:]
open(p, "w", encoding="utf-8").write(s)
print("spliced", i, j)
