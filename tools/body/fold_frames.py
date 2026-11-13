"""Frames of her posed body (and the R&D top + skirt on it) at the game's close cameras, for looking at the folds.

    python tools/body/fold_frames.py <round_dir> <out_dir> [--name N] [--frames "walk:10/back/mid,..."] [--no-render]

Python side (numpy, no Blender): poses the body exactly as foldcheck's "full" mode (LBS poser, Modes.pose with the rig's
drivers and correctives) and writes OBJs (body with UVs; the clothing pieces LBS-skinned by bone name with the same bone
worlds). Blender side (background, Eevee): tools/body/fold_frames_blender.py renders each frame bare and clothed.
It takes the "blender" turn for the renders (tools/turn.py) and gives it back at once. Produces no judgement.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import foldcheck as fc  # noqa: E402
import posers  # noqa: E402
from gl import Glb, weld  # noqa: E402

BLENDER = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
RDIR = fc.MARIONETTE / "generated/rnd/x14/r19"
CLOTHES = {"top": RDIR / "p1_top_rest.glb", "skirt": RDIR / "p1_skirt_rest.glb"}
ALBEDO = REPO / "godot/art/people/body_p1/albedo.png"
DEFAULT = ("walk:10/back/mid,walk:10/back/near,fight:20/front/near,fight:20/r34/near,fight:19/front/near,"
           "spine_flex/side_r/near,spine_flex/front/near")


def write_obj(path, V, T, UV=None, TUV=None):
    with open(path, "w") as f:
        np.savetxt(f, V, fmt="v %.6f %.6f %.6f")
        if UV is not None:
            np.savetxt(f, np.c_[UV[:, 0], 1.0 - UV[:, 1]], fmt="vt %.6f %.6f")
            for a, b in zip(T + 1, TUV + 1):
                f.write(f"f {a[0]}/{b[0]} {a[1]}/{b[1]} {a[2]}/{b[2]}\n")
        else:
            np.savetxt(f, T + 1, fmt="f %d %d %d")


def load_clothes(p):
    """name -> dict(P, T, J, W, ibm_by_poser_bone) for each clothing piece that carries a skin with our bone names."""
    out = {}
    for tag, path in CLOTHES.items():
        if not path.exists():
            print(f"  (no {path.name}: {tag} skipped)")
            continue
        g = Glb(str(path))
        if not g.js.get("skins"):
            print(f"  ({path.name} has no skin: clothing skipped)")
            continue
        sk = g.skeleton(0)
        m = next(m for m in g.meshes if m.node.startswith("piece_"))
        if m.J is None:
            print(f"  ({path.name} piece is not skinned: skipped)")
            continue
        miss = [n for n in sk.names if n not in p.index]
        k = np.array([p.index.get(n, -1) for n in sk.names])
        Wn = m.W / np.maximum(m.W.sum(1, keepdims=True), 1e-12)
        rep = weld(m.P.astype(float), 1e-6)
        T = rep[m.T]
        T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
        first = np.full(int(rep.max()) + 1, -1)
        first[rep[::-1]] = np.arange(len(rep))[::-1]
        out[tag] = dict(P=m.P.astype(float), J=m.J, W=Wn, ibm=sk.ibm, rest=sk.rest, map=k, T=T, first=first, miss=miss)
        print(f"  {tag}: {len(m.P)} pts, {len(sk.names)} joints, {len(miss)} not on the body skeleton")
    return out


def skin_piece(c, G):
    S = np.where((c["map"] >= 0)[:, None, None], G[np.maximum(c["map"], 0)] @ c["ibm"], c["rest"] @ c["ibm"])
    Ph = np.c_[c["P"], np.ones(len(c["P"]))]
    out = np.zeros((len(Ph), 3))
    for k in range(c["J"].shape[1]):
        out += c["W"][:, k:k + 1] * np.einsum("nij,nj->ni", S[c["J"][:, k]][:, :3, :], Ph)
    return out[c["first"]]


def build_objs(rd, od, frames):
    rd = Path(rd)
    rig = json.loads((rd / "rig.json").read_text())
    p = posers.make_poser("lbs", str(rd / "body.glb"), rig)
    sk = fc.Skin(p)
    md = fc.Modes(p, rig)
    body = p.glb.mesh(rig.get("body_mesh") or posers.guess_body(p.glb))
    UV = body.UV.astype(float)[:sk.nb]
    cl = load_clothes(p)
    need = {f[0] for f in frames}
    poses = {}
    for label, G, keyed in fc.rom_poses(p):
        if label in need and label not in poses:
            poses[label] = (G, keyed)
    for label, G, keyed in fc.rnd_poses(p, ["walk", "fight"]):
        if label in need:
            poses[label] = (G, keyed)
    info = {}
    od.mkdir(parents=True, exist_ok=True)
    pelvis = p.index["pelvis"]
    for label, (G, keyed) in poses.items():
        V = md.pose(G, keyed, "full")
        stem = label.replace(":", "-")
        Vw = V[:sk.nb][sk.first]
        T = sk.rep[sk.T]
        keep = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])
        write_obj(od / f"_{stem}_body.obj", Vw, T[keep], UV, sk.T[keep])
        files = {"body": f"_{stem}_body.obj"}
        for tag, c in cl.items():
            write_obj(od / f"_{stem}_{tag}.obj", skin_piece(c, G), c["T"])
            files[tag] = f"_{stem}_{tag}.obj"
        ph = G[pelvis][:3, 3]
        info[label] = {"files": files, "aim_xz": [float(ph[0]), float(ph[2])]}
    return info, bool(cl)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("round_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--name", help="round name for files (default: the folder name)")
    ap.add_argument("--frames", default=DEFAULT, help="pose/az/cam,... e.g. fight:20/front/near")
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args(argv)
    rd = Path(a.round_dir).resolve()
    name = a.name or rd.name
    od = Path(a.out_dir).resolve() / name
    od.mkdir(parents=True, exist_ok=True)
    frames = [tuple(s.split("/")) for s in a.frames.split(",")]
    t0 = time.time()
    info, clothed = build_objs(rd, od, frames)
    print(f"posed {len(info)} poses in {time.time() - t0:.0f} s", flush=True)
    job = {"name": name, "dir": str(od), "albedo": str(ALBEDO), "clothed": clothed, "poses": info,
           "frames": [{"pose": f[0], "az": f[1], "cam": f[2]} for f in frames]}
    (od / "job.json").write_text(json.dumps(job, indent=1))
    if a.no_render:
        return
    py = sys.executable
    rc = subprocess.call([py, str(REPO / "tools/turn.py"), "take", "blender", "body-posed fold frames", "--wait", "8", "--stale-ok"])
    if rc:
        sys.exit("blender turn not taken")
    try:
        t1 = time.time()
        rc = subprocess.call([BLENDER, "-b", "--factory-startup", "-P", str(HERE / "fold_frames_blender.py"), "--", str(od / "job.json")])
        n = len(list(od.glob(f"{name}_*.png")))
        print(f"blender rc {rc}; {n} pngs in {time.time() - t1:.0f} s")
    finally:
        subprocess.call([py, str(REPO / "tools/turn.py"), "give", "blender"])
    sheet(od, name, job)
    for f in od.glob("_*.obj"):
        f.unlink()


def sheet(od, name, job):
    from PIL import Image, ImageDraw
    cells = []
    for f in job["frames"]:
        for kind in ("bare", "clothed"):
            lab = f["pose"].replace(":", "-")
            fn = od / f"{name}_{lab}_{f['cam']}_{f['az']}_{kind}.png"
            if fn.exists():
                cells.append((fn, f"{f['pose']} {f['cam']} {f['az']} {kind}"))
    if not cells:
        return
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    S = Image.new("RGB", (cols * 480, rows * 270), (30, 30, 30))
    d = ImageDraw.Draw(S)
    for i, (fn, lab) in enumerate(cells):
        im = Image.open(fn).convert("RGB").resize((480, 270), Image.LANCZOS)
        x, y = (i % cols) * 480, (i // cols) * 270
        S.paste(im, (x, y))
        d.rectangle([x, y, x + 8 + 7 * len(lab), y + 14], fill=(0, 0, 0))
        d.text((x + 4, y + 2), lab, fill=(255, 255, 0))
    S.save(od / f"{name}_contact.png")
    print("contact sheet", od / f"{name}_contact.png")


if __name__ == "__main__":
    main()
