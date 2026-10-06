"""Forge.cs anew: the new layout and cards (forge_top, forge_mid) round the slurry's odds and the
hammer's moment kept from the old file."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\godot\src\Ui\Forge.cs"
old = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in old else "\n"
old = old.replace("\r\n", "\n")
odds_a = old.index("    /// <summary>The slurry's odds, seen before the jar is opened")
odds_b = old.index("    /// <summary>A jar of the Dig's slurry: Snib's three a day")
work = old.index("    void Work(Quote q, Action? sound = null, bool off = false)")
top = open(os.path.join(HERE, "forge_top.cs"), encoding="utf-8").read().replace("\r\n", "\n")
mid = open(os.path.join(HERE, "forge_mid.cs"), encoding="utf-8").read().replace("\r\n", "\n")
new = top.rstrip("\n") + "\n\n" + old[odds_a:odds_b].rstrip("\n") + "\n" + mid.rstrip("\n") + "\n\n" + old[work:]
open(P, "w", encoding="utf-8", newline="").write(new.replace("\n", nl))
print("ok", len(old.splitlines()), "->", len(new.splitlines()))
