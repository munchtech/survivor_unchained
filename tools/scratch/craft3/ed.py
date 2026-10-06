"""Exact replacements in a file, keeping its line endings: sub(path, [(old, new), ...])."""
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af01b0d61ef656dd4\godot"
import os


def sub(path, pairs, count=1):
    p = path if os.path.isabs(path) else os.path.join(ROOT, path)
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    for old, new in pairs:
        o, n = old.replace("\n", nl), new.replace("\n", nl)
        if o not in s:
            raise SystemExit(f"NOT FOUND in {path}: {old[:120]!r}")
        s = s.replace(o, n, count)
    open(p, "w", encoding="utf-8", newline="").write(s)
    print("ok", path)
