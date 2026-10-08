"""Copy the predecessor's perf6 scripts (tools/scratch/perf6) into this scratchpad's perf7 and
point them at this lead's worktree and scratchpad."""
import pathlib
import shutil

WT = pathlib.Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7afb4d33cdd5efba")
OLD = WT / "tools" / "scratch" / "perf6"
SP = pathlib.Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\perf7")
SP.mkdir(parents=True, exist_ok=True)
subs = [
    ("agent-a20bdef993e00f26b", "agent-a7afb4d33cdd5efba"),
    ("74e72383-70c7-41d5-8e96-2fad2ed58481", "0b33992d-1e38-4eb8-80a1-d5c23b1a44e6"),
    (r"scratchpad\perf5", r"scratchpad\perf7"),
]
for p in OLD.iterdir():
    if p.is_dir():
        continue
    dst = SP / p.name
    if p.suffix in (".py", ".ps1", ".txt", ".gdshaderinc"):
        t = p.read_text(encoding="utf-8-sig")
        for a, b in subs:
            t = t.replace(a, b)
        dst.write_text(t, encoding="utf-8")
        for line in t.splitlines():
            if "agent-a" in line or "scratchpad" in line:
                print(p.name, ":", line.strip()[:160])
    else:
        shutil.copy2(p, dst)
