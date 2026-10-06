import os, glob
S = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(os.path.dirname(S), "combat6")
os.makedirs(os.path.join(S, "logs"), exist_ok=True)
for f in glob.glob(os.path.join(src, "*.py")):
    if os.path.basename(f) == "setup.py": continue
    t = open(f, encoding="utf-8").read()
    for old in ("agent-a739d6792d21f5efd", "agent-a9f0d6c64d891d56d", "agent-a5115633c7006e4d4"):
        t = t.replace(old, "agent-a427a874da78cba8b")
    open(os.path.join(S, os.path.basename(f)), "w", encoding="utf-8").write(t)
    print("copied", os.path.basename(f))
