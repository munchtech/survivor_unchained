"""Exact text replacements in a worktree file, in place, bytes kept as they are otherwise.
Usage: python replace_s3.py FILE OLD NEW [COUNT] -- fails unless OLD occurs COUNT times (default: at least once)."""
import sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9"
rel, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
want = int(sys.argv[4]) if len(sys.argv) > 4 else None
p = WT + "\\" + rel.replace("/", "\\")
b = open(p, "rb").read()
o, n = old.encode("utf-8"), new.encode("utf-8")
k = b.count(o)
if k == 0 or (want is not None and k != want):
    sys.exit(f"{rel}: found {k}, wanted {want or 'some'}")
open(p, "wb").write(b.replace(o, n))
print(f"{rel}: replaced {k}")
