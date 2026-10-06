"""Copy the sixth writer's helper scripts into story7, pointed at this worktree."""
import os, re
SP = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1"
for f in ["show_s6.py", "jsonio_s6.py", "rules_s6.py", "seed_check_s6.py", "phrases_s6.py",
          "body_hours_s6.py", "genre_check_s6.py", "checks_s6.py", "crlf_s6.py"]:
    src = os.path.join(SP, "story6", f)
    if not os.path.exists(src):
        print("missing", f); continue
    s = open(src, encoding="utf-8").read()
    s = re.sub(r"C:\\Users\\munch\\Desktop\\survivorsunchained\\\.claude\\worktrees\\agent-[a-z0-9]+",
               lambda m: WT, s)
    s = s.replace("story6", "story7").replace("_s6", "_s7")
    open(os.path.join(SP, "story7", f.replace("_s6", "_s7")), "w", encoding="utf-8").write(s)
    print("ok", f)
