"""Copy the last crafting lead's helper scripts here, pointed at this worktree."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(os.path.dirname(HERE), "craft3")
for f in ["play.py", "crop.py", "sheet.py", "ed.py", "cut.py"]:
    s = open(os.path.join(OLD, f), encoding="utf-8-sig").read()
    s = s.replace("agent-af01b0d61ef656dd4", "agent-ab0b263c720bdbda8").replace("craft3", "craft4")
    open(os.path.join(HERE, f), "w", encoding="utf-8").write(s)
    print("ok", f)
