"""armor 5: the sheathed pieces' worst depth into her skin, split by WHERE (arm skin vs the rest), per key x outfit,
with the clip and frame. Uses the clearance file as it is (like armscheck --sockets --keep).
    python tools/scratch/armor5/sockdeep.py [clips...] [--step N] [--outfits a,b] [--json out.json]"""
import json, sys, time, argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "anim"))
import numpy as np
import armscheck as A

ARMY = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")


def job(args):
    outfit, folder, names, step = args
    ck = A.SocketChecker(outfit)
    clr = json.loads(A.CLEARANCE.read_text()).get(outfit, {})
    out = {}
    for name in names:
        Gs = ck.b.frames(ck.b.clip(name, Path(folder)))
        for f in range(0, len(Gs), step):
            G = Gs[f]; P = ck.b.pose(G); ck.body.pose(P)
            for k, d in ck.sheathed.items():
                push = d["normal"] * clr.get(d["socket"], 0.0)
                M = G[ck.I[d["bone"]]]
                Q = (ck.pts_s[k] + push) @ M[:3, :3].T + M[:3, 3]
                keep, near, _ = ck.measure(P, ck.body, Q)
                if keep.max() <= 0:
                    continue
                for j in np.nonzero(keep > 0)[0]:
                    pass
                # worst per region class
                wh = np.array([ck.where(near[j]) if keep[j] > 0 else "" for j in range(len(keep))])
                arm = np.array([any(a in w for a in ARMY) for w in wh])
                for cls, m in (("arm", arm & (keep > 0)), ("body", (~arm) & (keep > 0))):
                    if not m.any():
                        continue
                    j = int(np.argmax(np.where(m, keep, -1)))
                    rec = out.setdefault((k, cls), [0.0, "", -1, ""])
                    if keep[j] > rec[0]:
                        out[(k, cls)] = [round(float(keep[j]), 1), name, f, wh[j]]
    return outfit, {f"{k}|{c}": v for (k, c), v in out.items()}, {k: (d["kind"], d["socket"]) for k, d in ck.sheathed.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="*")
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--outfits", default=",".join(A.SOCKET_OUTFITS))
    ap.add_argument("--json")
    a = ap.parse_args()
    folder = A.OUTDIR / "clips"
    names = a.clips or ([f"idle_{c}" for c in A.CALLINGS if (folder / f"idle_{c}.json").exists()] + sorted(p.stem for p in folder.glob("*_town.json")))
    jobs = [(o, str(folder), names, a.step) for o in a.outfits.split(",")]
    res = {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        for o, r, info in ex.map(job, jobs):
            res[o] = r
    print(f"clips: {', '.join(names)} (step {a.step}), {time.time()-t0:.0f} s")
    print(f"{'key':28} {'outfit':9} {'where':5} {'mm':>6}  clip@frame  skin")
    for o in res:
        for kc, (mm, clip, f, w) in sorted(res[o].items()):
            k, c = kc.split("|")
            print(f"{k:28} {o:9} {c:5} {mm:6.1f}  {clip}@{f}  {w}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
