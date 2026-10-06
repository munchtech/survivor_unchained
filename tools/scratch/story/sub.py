"""Exact, counted text substitution in the worktree's files (fails loudly)."""
import os, sys
ROOT = r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a473fbc4762172b02/godot/"


def sub(path, old, new, count=1):
    p = os.path.join(ROOT, path)
    s = open(p, encoding='utf8', newline='').read()
    # Files are CRLF on this checkout; patterns are written with \n.
    crlf = '\r\n' in s
    o, n = (old.replace('\n', '\r\n'), new.replace('\n', '\r\n')) if crlf else (old, new)
    if s.count(o) != count:
        raise SystemExit(f"{path}: expected {count} of {old[:80]!r}, found {s.count(o)}")
    s = s.replace(o, n)
    open(p, 'w', encoding='utf8', newline='').write(s)
