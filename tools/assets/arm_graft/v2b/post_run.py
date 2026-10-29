"""Body 3's post chain on a freshly exported body (post steps 1, 2, 4, 5 and, with --reaver, 7): the nape, the breast
symmetry, the neck shape and relief, and the worn Reaver's post on an un-posted Reaver export.

    python tools/assets/arm_graft/v2b/post_run.py <src heroine.glb> <out dir> [--reaver <ref people dir>]

<out dir>/people/heroine.glb is posted in place (and copied to <out dir>/heroine.glb); with --reaver, the ref dir's
heroine_outfit_reaver.gltf/.bin and armor_tuck/ (a fresh outfits export, not yet posted) are copied beside it and
worn_reaver_post.py runs on that folder. Prints the body's post marks at the end. (Body 3, 23 Oct; in the repo from
Body 5 A2, paths repo-relative.)"""
import os
import shutil
import subprocess
import sys

A = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # tools/assets
sys.path.insert(0, A)
src, out = sys.argv[1], sys.argv[2]
ref = None
if "--reaver" in sys.argv:
    k = sys.argv.index("--reaver")
    if k + 1 >= len(sys.argv):
        raise SystemExit("--reaver needs the folder of an un-posted Reaver export (heroine_outfit_reaver.gltf/.bin, armor_tuck/)")
    ref = sys.argv[k + 1]
art = os.path.join(out, "people")
os.makedirs(art, exist_ok=True)
glb = os.path.join(art, "heroine.glb")
shutil.copyfile(src, glb)
import heroine_neck as h  # noqa: E402
import heroine_body_post as hbp  # noqa: E402
h.nape(glb, save=True, merge=False)
import breast_sym_post as bs  # noqa: E402
bs.correct(glb, glb)
import heroine_neck_shape as ns  # noqa: E402
ns.correct(glb, glb)
import heroine_neck_relief as nr  # noqa: E402
nr.run(glb, glb)
if ref is not None:
    for f in ("heroine_outfit_reaver.gltf", "heroine_outfit_reaver.bin"):
        shutil.copyfile(os.path.join(ref, f), os.path.join(art, f))
    shutil.copytree(os.path.join(ref, "armor_tuck"), os.path.join(art, "armor_tuck"), dirs_exist_ok=True)
    subprocess.run([sys.executable, os.path.join(A, "worn_reaver_post.py"), art], check=True)
shutil.copyfile(glb, os.path.join(out, "heroine.glb"))
print("MARKS", sorted(hbp.marks(os.path.join(out, "heroine.glb"))))
