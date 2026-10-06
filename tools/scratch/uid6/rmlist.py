"""Remove the files listed (one path per line, relative to the given root): python rmlist.py ROOT LIST"""
import os
import sys

root, lst = sys.argv[1], sys.argv[2]
n = 0
for line in open(lst, encoding='utf-8'):
    p = os.path.join(root, line.strip())
    if line.strip() and os.path.isfile(p):
        os.remove(p)
        n += 1
print('removed', n)
