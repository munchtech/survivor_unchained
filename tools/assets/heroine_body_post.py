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
     skin kept >= 1 mm under it); per-outfit config, only the arcanist (armor 14, the owner 21 Oct); then (s3)
     each cup's front as one round, full dome at the 3-6 cm scale (no apex highlight, no crease to the zip); then
     its baked convexity (UV2.y) over the cups baked again from that shape and made smooth (s2: it kept the old
     poke and hollow). Order: shell, dome, detail; the dome drops bust_detail so the bake follows it
                                                                    [outfit's bust_shell, bust_dome, bust_detail]
  4. heroine_neck_shape --art: her neck's taper, SCM, notch, clavicles, left = right; hair, outfits, armor pieces
     follow, records re-keyed (face 36)                                          [heroine_neck_shape]
  5. heroine_neck_relief: her collar's soft relief, a normal map on skin_graft (softened face 37: SOFT)  [heroine_neck_relief]
  6. heroine_arm_shape --art: her upper arms slimmer on the inner side (girth ~32 -> ~28.5 cm at 25-50%, tapering to
     the elbow), the armpit web slimmer from both sides, a small deltoid swell; hair, outfits, armor pieces follow,
     records re-keyed (armor 15, the owner 22 Oct)                                   [heroine_arm_shape]
  6b. heroine_ear_shape --art: her ears set closer to her head (each point in toward the fitted skull by a share of
     its stand-off: lobe 20 -> 12 mm, middle 19 -> 15, top 13 -> 10) and the ear's lower front join with her cheek
     rounded; hair, outfits, armor pieces follow, records re-keyed; then heroine_ear_ao.py again from the new shape
     (face 41, the owner 26 Oct: "lobe might stick too far away from head")         [heroine_ear_shape]
  7. heroine_brow_strokes: her own face's brows painted again as grown hairs, none crossing (the old strokes filled
     from the skin round them first), in head_tex/heroine_head.jpg, the paint the game lays over the glb's own copy;
     then heroine_browdye (Own's brows.png's core and skin from it). No glb is written: the LODs never carry her head
     (face 40, a max judge: the old strokes crossed in a lattice, "hatching")     [the paint's JPEG comment brow_strokes]
  7b. heroine_ear_shape --paint: every head paint's ear join (where the features' blue fades over the tragus and the
     lobe's front) laid as the blend of ear and cheek as they render, so her face's tone no longer warms the ear's
     already warmed paint into a pink band (face 41)                             [each paint's JPEG comment ear_join]
  7c. heroine_ear_shape --shade: the scalp shade (head_tex/heroine_shadow.png's green, laid by heroine_features.py)
     taken off her whole ear, front and tragus with it, faded back in over 0.5-3 mm into her scalp: under the pixie
     the ear's front third read hair-coloured (face 41, the owner 26 Oct)       [the PNG's text chunk ear_shade]
  8. worn_reaver_post: the reaver's channel of her vertex colours rebuilt from its slots' tuck records (the plain
     calling then tucks her under the wrap as the pieces path does), and the morph worn_reaver on her body (her
     breasts' undersides a little heavier, a soft roll under the wrap's lower edge, the outer side in; People.WornShape
     sets it while the reaver's top is worn) (armor 15 w1)                                    [worn_reaver]
  9. heroine_lod: the play LODs of every outfit, from the final body and pieces.

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
    if "heroine_arm_shape" not in m:
        run(os.path.join(HERE, "heroine_arm_shape.py"), "--art", art)
    if "heroine_ear_shape" not in m:
        run(os.path.join(HERE, "heroine_ear_shape.py"), "--art", art)
        run(os.path.join(HERE, "heroine_ear_ao.py"))
    paint = os.path.join(art, "head_tex", "heroine_head.jpg")
    if os.path.exists(paint):
        import heroine_brow_strokes as bs
        if bs.MARK not in bs.comment(paint):
            run(os.path.join(HERE, "heroine_brow_strokes.py"), art)
            run(os.path.join(HERE, "heroine_browdye.py"))
    # (each paint carries its own done-mark; the step skips a marked one)
    run(os.path.join(HERE, "heroine_ear_shape.py"), "--paint", art)
    # (the shade carries its own done-mark; heroine_features.py writes a new one without it)
    run(os.path.join(HERE, "heroine_ear_shape.py"), "--shade", art)
    # (the channel is rebuilt on every run, the morph only on a glb without it)
    run(os.path.join(HERE, "worn_reaver_post.py"), art)
    if "--no-lod" not in a:
        run(os.path.join(HERE, "heroine_lod.py"), art)
    print("BODY_POST: marks now", sorted(marks(glb)))


if __name__ == "__main__":
    main(sys.argv[1:])
