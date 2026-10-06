"""Replace lines [a, b) (1-based a, exclusive b) of a file with another file's text.
python splice.py FILE A B NEWTEXT_FILE"""
import sys
p, a, b, new = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
L = open(p, encoding="utf-8").read().split("\n")
N = open(new, encoding="utf-8").read().rstrip("\n").split("\n")
out = L[:a - 1] + N + L[b - 1:]
open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print(f"{p}: replaced {b - a} lines with {len(N)}")
