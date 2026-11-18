"""rnd_freeze: the R&D inputs of the body build, frozen into the repo (lane G, 16 Nov).

    python tools/body/rnd_freeze.py [--top GLB] [--walk GLB] [--fight GLB] [--top-cloth GLB]
                                    [--skirt-cloth GLB] [--out tools/body/base/rnd]

foldcheck (and through it build_topo's weights fold_relax and correctives shape_relax) read two things from
Marionette's git-ignored R&D scratch: the fitted top's rest surface (the strap regions) and the R&D walk/fight clips
(the "rnd" pose set). Scratch gets swept: x14/r19/p1_top_rest.glb was gone on 16 Nov and her_b no longer built
(KeyError strap_l). The build's inputs belong with the build, so this writes them once as small arrays:

  top.npz    pts: the top's piece_ mesh rest points, every 7th, mm (exactly what foldcheck.Skin queries)
  clips.npz  per tag (walk, fight): joints (skin joint names), S (keys, joints, 4, 4) = the clip's world @ its inverse
             bind per key (the part of rnd_poses that reads the glb), keyed (the names the clip keys)
  clothes.npz  per tag (top, skirt): fold_frames' arrays from the clothing glb (P, J, W normalized, ibm, rest, welded
             filtered T, first, joint names; no textures: fold_frames reads none from these glbs)
  freeze.json  the sources, their sizes and sha1, and the date

foldcheck uses these when present and falls back to the Marionette paths otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import foldcheck as fc  # noqa: E402
from gl import Glb  # noqa: E402

# 16 Nov: r19/p1_top_rest.glb is gone; r22/p1_top.glb is the same warden top (98,986 points), within 0.022 mm of the
# x14 and r11 copies at rest, and the latest of them (13 Nov 13:27)
TOP_SRC = fc.RND / "r22/p1_top.glb"
# fold_frames' clothed frames: r19/p1_{top,skirt}_rest.glb are gone; r22 has the same rig round's copies (13 Nov)
TOP_CLOTH = fc.RND / "r22/p1_top.glb"
SKIRT_CLOTH = fc.RND / "r22/p1_skirt.glb"


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def clip_arrays(path):
    sys.path.insert(0, str(fc.MARIONETTE / "tools/npc/attach"))
    import glbx  # noqa: E402
    j, b = glbx.read(str(path))
    an = j["animations"][0]
    keyed = sorted({j["nodes"][ch["target"]["node"]].get("name") for ch in an["channels"] if "node" in ch["target"]})
    sk = j["skins"][0]
    ibm = glbx.accessor(j, b, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    jn = [j["nodes"][n]["name"] for n in sk["joints"]]
    times = glbx.clip_times(j, b, 0)
    loc = glbx.clip_locals(j, b, 0, times)
    S = np.zeros((len(times), len(jn), 4, 4))
    for k in range(len(times)):
        Wd = glbx.worlds(j, loc[k])
        for i, n in enumerate(sk["joints"]):
            S[k, i] = Wd[n] @ ibm[i]
    return jn, S, keyed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", default=str(TOP_SRC))
    ap.add_argument("--walk", default=str(fc.RND_CLIPS["walk"]))
    ap.add_argument("--fight", default=str(fc.RND_CLIPS["fight"]))
    ap.add_argument("--top-cloth", default=str(TOP_CLOTH))
    ap.add_argument("--skirt-cloth", default=str(SKIRT_CLOTH))
    ap.add_argument("--out", default=str(fc.FROZEN))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    g = Glb(a.top)
    m = next(m for m in g.meshes if m.node.startswith("piece_"))
    pts = m.P.astype(float)[::7] * 1e3
    np.savez_compressed(out / "top.npz", pts=pts)
    arrs = {}
    for tag in ("walk", "fight"):
        jn, S, keyed = clip_arrays(getattr(a, tag))
        arrs[f"{tag}_joints"] = np.array(jn)
        arrs[f"{tag}_S"] = S
        arrs[f"{tag}_keyed"] = np.array(keyed)
        print(tag, S.shape, len(keyed), "keyed")
    np.savez_compressed(out / "clips.npz", **arrs)
    import fold_frames as ff
    carr = {}
    for tag, path in (("top", a.top_cloth), ("skirt", a.skirt_cloth)):
        for k, v in ff.cloth_arrays(path).items():
            carr[f"{tag}_{k}"] = v
    np.savez_compressed(out / "clothes.npz", **carr)
    src = {k: {"path": str(Path(p)).replace("\\", "/"), "bytes": Path(p).stat().st_size, "sha1": sha1(p)}
           for k, p in (("top", a.top), ("walk", a.walk), ("fight", a.fight),
                         ("top_cloth", a.top_cloth), ("skirt_cloth", a.skirt_cloth))}
    info = {"date": time.strftime("%Y-%m-%d %H:%M"), "sources": src, "top_node": m.node, "top_points": int(len(pts)),
            "why": "the body build read these from Marionette's git-ignored R&D scratch; r19/p1_top_rest.glb was swept "
                   "by 16 Nov (her_b failed: KeyError strap_l). r19 is gone, so the top is r22's copy of the same piece. "
                   "clothes.npz: fold_frames read r19/p1_top_rest.glb and p1_skirt_rest.glb (swept); frozen from r22's p1_top.glb and p1_skirt.glb."}
    (out / "freeze.json").write_text(json.dumps(info, indent=1))
    print("wrote", out, pts.shape)


if __name__ == "__main__":
    main()
