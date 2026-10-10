"""Perf8 setup: copy git-ignored .import/.uid files from the predecessor's worktree into this one,
and copy the scratchpad perf7 scripts into scratchpad perf8, pointed at this worktree."""
import os, pathlib, shutil

OLDWT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7afb4d33cdd5efba"
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6a04e32348559b6c"
SP = pathlib.Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad")
for sub in (r"public\assets", r"godot"):
    copied = 0
    for root, dirs, files in os.walk(os.path.join(OLDWT, sub)):
        dirs[:] = [d for d in dirs if d not in (".godot", "assets", "bin", "obj", ".shots")]
        for f in files:
            if not (f.endswith(".import") or f.endswith(".uid")):
                continue
            rel = os.path.relpath(os.path.join(root, f), OLDWT)
            dst = os.path.join(WT, rel)
            if os.path.exists(dst) or not os.path.exists(dst.rsplit(".", 1)[0]):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)
            copied += 1
    print(sub, "copied", copied)
src, dst = SP / "perf7", SP / "perf8"
dst.mkdir(exist_ok=True)
subs = [("agent-a7afb4d33cdd5efba", "agent-a6a04e32348559b6c"), (r"scratchpad\perf7", r"scratchpad\perf8"), ("scratchpad/perf7", "scratchpad/perf8")]
for p in src.iterdir():
    if p.is_dir():
        continue
    if p.suffix in (".py", ".ps1", ".txt", ".gdshaderinc"):
        t = p.read_text(encoding="utf-8-sig")
        for a, b in subs:
            t = t.replace(a, b)
        (dst / p.name).write_text(t, encoding="utf-8")
    else:
        shutil.copy2(p, dst / p.name)
print(sorted(x.name for x in dst.iterdir()))
