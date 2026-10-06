"""Revert .import files a headless import rewrote, and drop the .uid files it made for others'
scripts (keeping our own). Runs git in the crafting worktree only."""
import subprocess
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7debf1459f14dfe7"
KEEP_UID = {"godot/src/Ui/StillRoom.cs.uid", "godot/tests/CraftersTests.cs.uid"}
lines = subprocess.run(["git", "status", "--short"], cwd=WT, capture_output=True, text=True).stdout.splitlines()
mod = [l[3:] for l in lines if l.startswith(" M") and l.endswith(".import")]
for i in range(0, len(mod), 100):
    subprocess.run(["git", "checkout", "--"] + mod[i:i + 100], cwd=WT, check=True)
print("reverted", len(mod))
import os
gone = 0
for l in lines:
    p = l[3:]
    if l.startswith("??") and p.endswith(".uid") and p not in KEEP_UID:
        os.remove(os.path.join(WT, p)); gone += 1
print("removed uids", gone)
