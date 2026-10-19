"""python writeall.py <piece> <WRAP key> <solve.py out json> [--seat]: the wrap into keyed.py, and the seat into
WeaponSockets.cs (fistfit.write_seat), printing the seat's move in mm."""
import sys, json
import numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim")
import fistfit as F
piece, key, path = sys.argv[1:4]
d = json.load(open(path)); w = d["wrap"]
w["bends"] = {k: tuple(v) for k, v in w["bends"].items()}
F.write_wrap(key, w)
if "--seat" in sys.argv:
    A0, _ = F.read_seat(piece); A = np.array(d["A"])
    F.write_seat(piece, A)
    print("seat", F.PIECES[piece]["at"], np.round(A0 * 1000, 1).tolist(), "->", np.round(A * 1000, 1).tolist(),
          f"moved {np.linalg.norm(A - A0) * 1000:.1f} mm")
print("written", key)
