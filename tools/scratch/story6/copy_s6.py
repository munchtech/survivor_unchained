"""Copy the fifth lead's story checks into story6, pointed at this worktree."""
import os
S = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(S), "story5")
for n in ["jsonio", "show", "seed_check", "phrases", "body_hours", "genre_check", "rules", "crlf", "slots"]:
    t = open(os.path.join(SRC, f"{n}_s5.py"), encoding="utf-8").read()
    t = t.replace("agent-a54dc034ed29f2e02", "agent-a7ba8903f4c8261b1").replace("jsonio_s5", "jsonio_s6")
    open(os.path.join(S, f"{n}_s6.py"), "w", encoding="utf-8").write(t)
    print("copied", n)
