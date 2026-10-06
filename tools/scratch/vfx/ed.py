"""Exact replacements in a worktree file, whatever its line endings: edit(rel, [(old, new), ...])."""
import io
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545\godot"


def edit(rel, pairs):
    p = WT + "\\" + rel
    raw = io.open(p, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    for a, b in pairs:
        n = s.count(a)
        assert n == 1, (rel, n, a[:120])
        s = s.replace(a, b)
    if crlf:
        s = s.replace("\n", "\r\n")
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("edited", rel)
