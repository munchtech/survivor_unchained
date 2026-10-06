import os, shutil, glob
S = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(os.path.dirname(S), "combat5")
for f in glob.glob(os.path.join(src, "*.py")):
    t = open(f, encoding="utf-8").read().replace("agent-a5115633c7006e4d4", "agent-a739d6792d21f5efd")
    open(os.path.join(S, os.path.basename(f)), "w", encoding="utf-8").write(t)
    print("copied", os.path.basename(f))
