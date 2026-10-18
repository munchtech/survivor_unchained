# Pokes of her lower teeth/gum through her chin skin at the game's used expressions (cinematics: mouth_open <=0.25, smile <=0.15, frown <=0.2)
import sys, os, inspect, re
os.environ["GUMLOW_DEBUG"] = "1"
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import heroine_mouth_inner as mi, heroine_seam as hs
share = sys.argv[2] == "share"
src = inspect.getsource(mi.gum_low)
if not share:
    src = src.replace('for sl in ("mouth_height-", "mouth_height+"):', 'for sl in ():')
src = src.replace('if "gum_low" in tm.get("extras", {}):', 'if False:')
mi.GUMLOW_POSES = ({"mouth_open": 0.12}, {"mouth_open": 0.25}, {"mouth_open": 0.25, "smile": 0.15}, {"mouth_open": 0.25, "frown": 0.2})
mi.GUMLOW_MM = float(sys.argv[3])
ns = vars(mi)
exec(compile(src, "gl", "exec"), ns)
js, binc = hs._load(sys.argv[1])
chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
print("RESULT", ns["gum_low"](js, binc, chunks))
