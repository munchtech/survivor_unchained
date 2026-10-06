"""Is commit A in branch B? python contains.py COMMIT REF [COMMIT REF ...]"""
import subprocess, sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b"
a = sys.argv[1:]
for c, r in zip(a[::2], a[1::2]):
    rc = subprocess.run(["git", "merge-base", "--is-ancestor", c, r], cwd=WT).returncode
    print(c, "in" if rc == 0 else "NOT in", r)
