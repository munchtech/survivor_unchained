"""List clips whose hand or forearm spins more than a threshold in a frame,
with the frames. Usage: python spin.py [thresh] [names...]"""
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import audit  # noqa: E402
from rig import DATA, Skeleton  # noqa: E402

th = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
want = sys.argv[2:]
n = 0
for label, folder, skel in audit.SETS:
    sk = Skeleton.load(DATA / skel)
    files = sorted(folder.glob("*.json"))
    if label == "folk_f":
        files = [f for f in files if f.stem.startswith("f_")]
    if label == "folk_m":
        files = [f for f in files if f.stem.startswith("m_")]
    for f in files:
        if want and not any(w in f.stem for w in want):
            continue
        d, out = audit.audit(f, sk)
        hits = []
        for s in "lr":
            for fr, why in out[s]["flags"]:
                for part in why.split("; "):
                    if "spins" in part or "turns" in part:
                        v = float(part.split()[2])
                        if v > th:
                            hits.append(f"{s}f{fr}:{part}")
        if hits:
            n += 1
            print(f"{label:6s} {f.stem:28s} " + ", ".join(hits))
print(n, "clips")
