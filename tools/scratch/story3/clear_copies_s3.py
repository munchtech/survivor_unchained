"""Remove the untracked art copies in this worktree that the integration branch now tracks,
so the merge can bring the tracked versions in. Only untracked files under godot/art are touched."""
import os, subprocess
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9"
def git(*a):
    return subprocess.run(["git", "-C", WT, *a], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
untracked = set(git("ls-files", "--others", "--exclude-standard"))
tracked_there = set(git("ls-tree", "-r", "--name-only", "origin/claude/vigilant-galileo-l6jqyx"))
gone = sorted(f for f in untracked & tracked_there if f.startswith("godot/art/"))
for f in gone:
    os.remove(os.path.join(WT, f.replace("/", os.sep)))
print(len(gone), "removed; untracked left:", len(untracked) - len(gone))
