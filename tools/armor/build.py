"""Build armor pieces on her body (docs/handoff/armor.md 1.6).

    python tools/armor/build.py <id> [<id> ...] | --all  [--src <heroine_built.blend>]

Each piece is godot/art/armor/src/<id>/piece.json; tools/armor/piece_blender.py builds it in Blender (headless)
on the outfit build's source scene and her body prep, and writes godot/art/armor/<id>.gltf + .bin,
armor_tuck/<id>.bin, <id>.sockets.json and its row in armor_index.json. Scratch (and each run's log and numbers)
goes to .shots/armor2/build/<id>/ (git-ignored). Take a blender turn first (tools/turn.py take blender ...).
It never writes the four outfit files, heroine.glb or godot/art/outfit; it checks that afterwards.
"""
import glob
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BLENDER = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
# (the outfit build's source scene, copied out of the 181eef02 session's Temp scratchpad (outfits\hs) on 18 Oct;
# its 10 images are all packed, so it resolves wherever it lies. docs/handoff/outfits.md names the copy. SRC overrides.)
SRC = os.environ.get("SRC", r"C:\Users\munch\Desktop\survivorsunchained_inputs\armor_src\heroine_built.blend")
GUARD = ["godot/art/outfit", "godot/art/people/heroine.glb", "godot/art/people/heroine_outfit_warden.gltf",
         "godot/art/people/heroine_outfit_arcanist.gltf", "godot/art/people/heroine_outfit_ranger.gltf",
         "godot/art/people/heroine_outfit_reaver.gltf", "godot/art/people/outfit_tex", "tools/assets/heroine_neck_graft.npz"]


def dirty(paths):
    out = subprocess.run(["git", "status", "--porcelain", "--"] + paths, cwd=ROOT, capture_output=True, text=True).stdout
    return sorted(l[3:] for l in out.splitlines() if not l[3:].endswith((".import", ".uid")))


def build(pid, src):
    pj = os.path.join(ROOT, "godot", "art", "armor", "src", pid, "piece.json")
    scratch = os.path.join(ROOT, ".shots", "armor2", "build", pid)
    os.makedirs(scratch, exist_ok=True)
    before = dirty(GUARD)
    t0 = time.time()
    log = os.path.join(scratch, "build.log")
    with open(log, "w", encoding="utf-8") as fh:
        r = subprocess.run([BLENDER, "-b", src, "--python", os.path.join(ROOT, "tools", "armor", "piece_blender.py"), "--", pj, scratch],
                           cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    wall = time.time() - t0
    after = dirty(GUARD)
    touched = sorted(set(after) - set(before))
    text = open(log, encoding="utf-8", errors="replace").read()
    ok = r.returncode == 0 and "ARMOR NUMBERS" in text and "ARMOR REFUSED" not in text
    for l in text.splitlines():
        if l.startswith(("ARMOR REFUSED", "Traceback")):
            print(l)
    print("BUILD %s: %s in %.0f s (log %s)" % (pid, "ok" if ok else "FAILED (exit %d)" % r.returncode, wall, log))
    if ok:
        # (its gameplay and shadow LODs, appended to the fresh export: tools/armor/piece_lod.py)
        gl_ = os.path.join(ROOT, "godot", "art", "armor", pid + ".gltf")
        r2 = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "armor", "piece_lod.py"), gl_, "--numbers",
                             os.path.join(scratch, "numbers.json")], cwd=ROOT, capture_output=True, text=True)
        print((r2.stdout + r2.stderr).strip())
        ok = r2.returncode == 0
        # (imported as the outfits are: Godot's own LODs off, ours are in the file)
        imp = gl_ + ".import"
        if not os.path.exists(imp):
            ref = os.path.join(ROOT, "godot", "art", "people", "heroine_outfit_warden.gltf.import")
            keep = [l for l in open(ref, encoding="utf-8").read().splitlines()
                    if not l.startswith(("uid=", "path=", "dest_files=", "source_file="))]
            open(imp, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join(keep) + chr(10))
    if touched:
        print("BUILD %s: WROTE GUARDED FILES %s" % (pid, touched))
        ok = False
    return ok


def main(argv):
    src = argv[argv.index("--src") + 1] if "--src" in argv else SRC
    ids = [a for a in argv if not a.startswith("--") and a != src]
    if "--all" in argv:
        ids = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "godot", "art", "armor", "src", "*", "piece.json")))
    if not os.path.exists(os.path.join(ROOT, "godot", "art", "armor", "trim_strip.json")):
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "armor", "trim_strip.py")], check=True)
    bad = [p for p in ids if not build(p, src)]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
