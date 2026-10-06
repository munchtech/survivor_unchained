import os
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in ["prev.py", "jedit.py", "times.py", "frames.py"]:
    t = open(os.path.join(S, "cin2", f), encoding="utf-8").read()
    t = t.replace("agent-a3058a45eee41d695", "agent-a79b6d8c81e14dc63")
    open(os.path.join(S, "cin3", f), "w", encoding="utf-8", newline="\n").write(t)
    print(f, "agent-a79b6d8c81e14dc63" in t)
