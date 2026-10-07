"""Copy the old perf5 scratch scripts here and point them at this lead's worktree and scratchpad."""
import pathlib
import shutil

OLD = pathlib.Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf5")
SP = pathlib.Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\perf5")
SP.mkdir(parents=True, exist_ok=True)
for f in ["batch1.ps1", "copy_imports.py", "crops.py", "runs1.txt", "runs0.txt", "shoot.py"]:
    shutil.copy2(OLD / f, SP / f)
subs = [
    (r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5", r"C:\Users\munch\Desktop\survivorsunchained"),
    ("agent-ad57a6dd0798688d7", "agent-a20bdef993e00f26b"),
    (r"C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3", r"C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481"),
]
for f in ["batch1.ps1", "copy_imports.py", "crops.py", "shoot.py"]:
    p = SP / f
    t = p.read_text(encoding="utf-8-sig")
    for a, b in subs:
        t = t.replace(a, b)
    p.write_text(t, encoding="utf-8")
    for line in t.splitlines():
        if "survivorsunchained" in line or "scratchpad" in line:
            print(f, ":", line.strip()[:220])
