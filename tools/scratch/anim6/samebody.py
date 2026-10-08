"""Is the built body the same as before, bar its helper weights? Positions,
normals, UVs and triangle lists per mesh; joints listed; weights changed where."""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8d33b2672b7be905\tools\anim")
import numpy as np  # noqa: E402
from skin import Gltf  # noqa: E402

S = Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\an")
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8d33b2672b7be905")


def meshes(path):
    g = Gltf(path)
    js = g.js
    out = {}
    for n in js["nodes"]:
        if "mesh" not in n:
            continue
        m = js["meshes"][n["mesh"]]
        joints = [js["nodes"][j]["name"] for j in js["skins"][n["skin"]]["joints"]] if "skin" in n else []
        prims = []
        for pr in m["primitives"]:
            a = pr["attributes"]
            d = {k: g.accessor(v) for k, v in a.items() if k in ("POSITION", "NORMAL", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0")}
            d["idx"] = g.accessor(pr["indices"]) if "indices" in pr else None
            prims.append(d)
        out[n["name"]] = (joints, prims)
    return out


for name in ["heroine.glb"] + [f"heroine_outfit_{o}.gltf" for o in ("warden", "arcanist", "ranger", "reaver")]:
    a, b = meshes(S / "before" / "people" / name), meshes(WT / "godot" / "art" / "people" / name)
    print("==", name, "meshes", len(a), len(b), "same names" if set(a) == set(b) else f"DIFFERENT {set(a) ^ set(b)}")
    for k in sorted(set(a) & set(b)):
        ja, pa = a[k]
        jb, pb = b[k]
        extra = [j for j in jb if j not in ja]
        missing = [j for j in ja if j not in jb]
        rep = []
        for p, q in zip(pa, pb):
            for key in ("POSITION", "NORMAL", "TEXCOORD_0"):
                if key in p and key in q:
                    if p[key].shape != q[key].shape:
                        rep.append(f"{key} shape {p[key].shape} vs {q[key].shape}")
                    else:
                        rep.append(f"{key} {np.abs(p[key].astype(float) - q[key].astype(float)).max():.2e}")
            if p["idx"] is not None and q["idx"] is not None:
                rep.append("idx same" if p["idx"].shape == q["idx"].shape and (p["idx"] == q["idx"]).all() else "idx DIFF")
            if "WEIGHTS_0" in p and p["POSITION"].shape == q["POSITION"].shape:
                # dense weights by joint name, compared
                def dense(J, W, names):
                    D = {}
                    for i in range(4):
                        for nm in set(names[j] for j in np.unique(J[:, i])):
                            pass
                    return None
                wa = np.zeros((len(p["POSITION"]), len(set(ja) | set(jb))))
                allj = sorted(set(ja) | set(jb))
                ix = {n: i for i, n in enumerate(allj)}
                wb = np.zeros_like(wa)
                for i in range(4):
                    np.add.at(wa, (np.arange(len(wa)), [ix[ja[j]] for j in p["JOINTS_0"][:, i]]), p["WEIGHTS_0"][:, i].astype(float))
                    np.add.at(wb, (np.arange(len(wb)), [ix[jb[j]] for j in q["JOINTS_0"][:, i]]), q["WEIGHTS_0"][:, i].astype(float))
                ch = np.abs(wa - wb).sum(1) > 1e-3
                rep.append(f"weights changed at {ch.sum()} of {len(wa)}")
        print(f"  {k}: +{len(extra)} joints {extra[:3]}{'...' if len(extra) > 3 else ''} -{len(missing)}; " + "; ".join(rep[:12]))
