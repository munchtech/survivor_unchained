"""Move untracked merge blockers aside (to scratch) and list tracked ones for restore."""
import os, shutil, subprocess
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
S = os.path.dirname(os.path.abspath(__file__))
paths = [l.strip() for l in open(os.path.join(S, "merge_blockers.txt"), encoding="utf8") if l.strip() and not l.startswith("Please")]
tracked = set(subprocess.run(["git", "-C", WT, "ls-files"], capture_output=True, text=True).stdout.split("\n"))
restore, moved = [], 0
for p in paths:
    if p in tracked:
        restore.append(p)
    elif os.path.exists(os.path.join(WT, p)):
        dst = os.path.join(S, "merge_aside", p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(WT, p), dst)
        moved += 1
if restore:
    subprocess.run(["git", "-C", WT, "checkout", "--"] + restore)
print("moved", moved, "restored", len(restore))
