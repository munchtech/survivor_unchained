"""ts.py <src.glb> <dst.glb> [ease|noease] [K=V ...]: heroine_throat.ease (unless noease) then soften(dst, 0) (the glb cut already)."""
import sys, shutil, time
sys.path.insert(0, "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe/tools/assets")
import heroine_throat_skin as ht
src, dst, mode = sys.argv[1], sys.argv[2], sys.argv[3]
for k in sys.argv[4:]:
    a, b = k.split("=")
    try:
        b = eval(b)
    except Exception:
        pass
    setattr(ht, a, b)
shutil.copy(src, dst)
if mode == "ease":
    ht.ease(dst)
t = time.time()
ht.soften(dst, 0.0)
print("soften %.1f s" % (time.time() - t))
