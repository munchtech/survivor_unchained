"""Her body's post-steps after a body build, in order, on the built art (face 36, 21 October 2026).

Until now the chain lived in a lead's scratch (armor 8's rebuild/nape_post.py). The recipe that matches integration:
a full build with NAPE=0, then this, then the install (build.py --all, cover.py for changed pieces), then a headless
reimport. Each step marks the glb it changed and skips a marked one, so a second run changes nothing; but the pieces'
and hair's follow is only safe on files the build just wrote (match_pieces is not idempotent): run this once per
fresh export, and restore tools/assets/heroine_neck_graft.npz from git after every build.

  1. nape (heroine_neck.nape, weights only, merge off), the outfits' points that took those weights follow
     (match_pieces), and the straps' rows evened again (strap_rows.even)       [done-mark heroine_nape]
  2. breast_sym_post --no-follow: her left breast's inner slope onto her right's mirror; records re-keyed, no slot
     piece touched; the four outfits' points over it follow her skin (armor 14: the bodysuit had kept the old
     hollow), each outfit marked breast_sym_follow (armor 12, the owner's dent)  [breast_sym]
  3. bust_shell_post: the arcanist bodysuit's leather over her cups as a smooth, full shell (no hollow at her left
     lower inner breast, no lumps along the zip edges, no nipple pokes; the stitching and piping carried, her tucked
     skin kept >= 1 mm under it); per-outfit config, only the arcanist (armor 14, the owner 21 Oct); then its
     baked convexity (UV2.y) over the cups made smooth to match (s2: it kept the old poke and hollow)
                                                                    [outfit's bust_shell, bust_detail]
  4. heroine_neck_shape --art: her neck's taper, SCM, notch, clavicles, left = right; hair, outfits, armor pieces
     follow, records re-keyed (face 36)                                          [heroine_neck_shape]
  5. heroine_neck_relief: her collar's soft relief, a normal map on skin_graft (softened face 37: SOFT)  [heroine_neck_relief]
  6. heroine_lod: the play LODs of every outfit, from the final body and pieces.

    python tools/assets/heroine_body_post.py [art dir, default godot/art/people] [--skip-nape] [--no-lod]
"""
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUTFITS = ("warden", "arcanist", "ranger", "reaver")


def marks(glb):
    with open(glb, "rb") as f:
        f.read(12)
        n = struct.unpack("<I", f.read(4))[0]
        f.read(4)
        j = json.loads(f.read(n))
    return set(((j.get("asset") or {}).get("extras") or {}).keys()) | set((j.get("extras") or {}).keys())


def run(*args):
    print("BODY_POST:", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], check=True)


def main(a):
    art = next((x for x in a if not x.startswith("--")), "godot/art/people")
    glb = os.path.join(art, "heroine.glb")
    if "--skip-nape" not in a and "heroine_nape" not in marks(glb):
        import heroine_neck as h
        import strap_rows
        fld = h.nape(glb, save=True, merge=False)
        for o in OUTFITS:
            p = os.path.join(art, f"heroine_outfit_{o}.gltf")
            if os.path.exists(p):
                h.match_pieces(p, fld)
        for o in OUTFITS:
            p = os.path.join(art, f"heroine_outfit_{o}.gltf")
            if os.path.exists(p):
                strap_rows.even(p)
    else:
        print("BODY_POST: nape already on the glb (or skipped)")
    m = marks(glb)
    if "breast_sym" not in m:
        run(os.path.join(HERE, "breast_sym_post.py"), "--art", art, "--no-follow")
    # (the outfit carries its own done-mark; the step skips a file that has it)
    run(os.path.join(HERE, "bust_shell_post.py"), art, "arcanist")
    if "heroine_neck_shape" not in m:
        run(os.path.join(HERE, "heroine_neck_shape.py"), "--art", art)
    if "heroine_neck_relief" not in m:
        run(os.path.join(HERE, "heroine_neck_relief.py"), glb, glb)
    if "--no-lod" not in a:
        run(os.path.join(HERE, "heroine_lod.py"), art)
    print("BODY_POST: marks now", sorted(marks(glb)))


if __name__ == "__main__":
    main(sys.argv[1:])
