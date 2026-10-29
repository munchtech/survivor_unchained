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
     RETIRED (armor 18 g2b): baked into heroine_built_armroot.blend; runs only with --arm-shape (pre-graft blend).
  6a. (retired, armor 17 N3) arc_fit_post fitted the arcanist's caps and evened its collar on the built gltf (armor 16
     N1); a max judge failed both as cut. heroine_outfits.py now cuts them right: caps ending above her deltoid's bulge,
     CAP_LIFT off her and CAP_THICK of the leather's thickness (THIN_ZONE), and the collar cut on her Head weight made
     the same both sides (KEEP_SYM). Not run.
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
  7d. heroine_ear_shape --tick: every head paint's crease line where her tragus meets her cheek (darker and redder
     than its 1.5 mm neighbourhood) eased by half: a dark red tick at the Look turned 40 (face 42)
                                                                                 [each paint's JPEG comment ear_tick]
  7e. heroine_ear_shape --front: every head paint's ear front (helix root to tragus) laid darker by its own gap to its
     cheek and a little richer: it rendered a pale grey strip by her cheek at the Look turned 40 (face 42); its mask
     smooth along the ear (face 43: a comb mask had left a ladder of pale bars)
                                                                               [each paint's JPEG comment ear_front]
  8. worn_reaver_post: the reaver's channel of her vertex colours rebuilt from its slots' tuck records (the plain
     calling then tucks her under the wrap as the pieces path does), and the morph worn_reaver on her body (her
     breasts' undersides a little heavier, a soft roll under the wrap's lower edge, the outer side in; People.WornShape
     sets it while the reaver's top is worn) (armor 15 w1)                                    [worn_reaver]
  8b. axilla_fold_post: her pec fold as an arm rises, the morphs axilla_fold_l/r (a ridge along the pec's outer edge,
     an armpit hollow behind it) and raise_crease_l/r (the crease under each breast half filled, its lower edge's
     shear smoothed), authored on her posed shape at full raise; HerRaise drives them per side; the arcanist, ranger
     and reaver tops and pauldrons carry the same morphs (they follow her skin) (armor 16 R1)  [axilla_fold; outfit's axilla_fold]
  8c. shoulder_psd_post: her shoulders and armpits as an arm rises, pose-space correctives shoulder_{abd117,abd140,
     flex117,flex140,up175,abd140s,flex140s,up175s}_l/r, authored with HerShrug's clavicle lift (helpers.shrug; the s
     ones 30 deg past it): delta-mush targets, then sculpted (a deltoid cap, the pec and lat folds as webs over the
     pit's crease, the hollow between, folded faces untangled) (armor 17 C1, C2); HerRaise drives them from each upper
     arm's direction in her torso frame (Play/ShoulderPsd); every outfit's tops, cloak and collar carry them, the
     pauldrons the whole of the shoulder's move  [shoulder_psd; outfit's shoulder_psd, shoulder_psd_pauldrons]
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
    # (6 heroine_arm_shape retired, armor 18 g2b: its field is baked into the arm-root graft's blend,
    # heroine_built_armroot.blend, with the pit fairing; see tools/assets/arm_graft/g2b/README.md. Applied here too
    # it would slim her arms twice. The step's code stays for a build from the pre-graft blend.)
    if "--arm-shape" in a and "heroine_arm_shape" not in m:
        run(os.path.join(HERE, "heroine_arm_shape.py"), "--art", art)
    # (6a arc_fit_post retired, armor 17 N3: the caps and collar are cut right in heroine_outfits.py itself)
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
    run(os.path.join(HERE, "heroine_ear_shape.py"), "--tick", art)
    run(os.path.join(HERE, "heroine_ear_shape.py"), "--front", art)
    # (the channel is rebuilt on every run, the morph only on a glb without it)
    run(os.path.join(HERE, "worn_reaver_post.py"), art)
    # (the body's morphs skipped when on the glb, each outfit's follow when its file is marked)
    run(os.path.join(HERE, "axilla_fold_post.py"), art)
    run(os.path.join(HERE, "shoulder_psd_post.py"), art)
    if "--no-lod" not in a:
        run(os.path.join(HERE, "heroine_lod.py"), art)
    print("BODY_POST: marks now", sorted(marks(glb)))


if __name__ == "__main__":
    main(sys.argv[1:])
