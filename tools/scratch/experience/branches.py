"""What each collaborator's branch holds beyond our HEAD: python branches.py [agent ids...]"""
import subprocess, sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b"
ids = sys.argv[1:] or ["afe45df4957917614", "abc6bbe020c7fe287", "aab47bfdab5955dac",
                       "a26767f7f9955cb56", "a7ba8903f4c8261b1", "a03acf30b3e9bdd70"]
def git(*a):
    return subprocess.run(["git", *a], cwd=WT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
for i in ids:
    ref = "origin/worktree-agent-" + i
    ahead = git("rev-list", "--count", "HEAD.." + ref)
    print(f"== {i}  ahead of HEAD: {ahead or '?'}")
    print(git("log", "--format=%h %ci %s", "-6", "HEAD.." + ref))
