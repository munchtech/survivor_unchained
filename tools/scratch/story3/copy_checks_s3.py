"""Copy the predecessor's story checks into story3, pointed at this worktree."""
import os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(os.path.dirname(here), "story2")
for name in ("seed_check", "body_hours", "phrases"):
    t = open(os.path.join(src, name + "_s2.py"), encoding="utf-8").read()
    t = t.replace("agent-a035208561a66c171", "agent-a73ca9d35d0c487a9")
    open(os.path.join(here, name + "_s3.py"), "w", encoding="utf-8").write(t)
print("copied")
