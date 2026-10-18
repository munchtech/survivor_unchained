import sys,shutil; sys.path.insert(0,"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe/tools/assets")
import heroine_throat as ht
for k in sys.argv[3:]:
    a,b=k.split("=")
    try: b=float(b)
    except ValueError: pass
    setattr(ht,a,b)
shutil.copy(sys.argv[1],sys.argv[2]); ht.ease(sys.argv[2])
