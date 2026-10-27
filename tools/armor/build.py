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
# its 10 images are all packed, so it resolves wherever it lies. docs/handoff/outfits.md names the copy. SRC overrides. Armor 18 g3, 22 Oct: the arm-root graft blend, the body now installed.)
SRC = os.environ.get("SRC", r"C:\Users\munch\Desktop\survivorsunchained_inputs\armor_src\heroine_built_armroot.blend")
GUARD = ["godot/art/outfit", "godot/art/people/heroine.glb", "godot/art/people/heroine_outfit_warden.gltf",
         "godot/art/people/heroine_outfit_arcanist.gltf", "godot/art/people/heroine_outfit_ranger.gltf",
         "godot/art/people/heroine_outfit_reaver.gltf", "godot/art/people/outfit_tex", "tools/assets/heroine_neck_graft.npz"]


def dirty(paths):
    out = subprocess.run(["git", "status", "--porcelain", "--"] + paths, cwd=ROOT, capture_output=True, text=True).stdout
    return sorted(l[3:] for l in out.splitlines() if not l[3:].endswith((".import", ".uid")))


def adorn(pid, post=False):
    """tools/armor/adorn.py: a variant's whole build (its base's shell copied), or a Blender build's other adornment."""
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "armor", "adorn.py"), pid] + (["--post"] if post else []),
                       cwd=ROOT, capture_output=True, text=True)
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith(("ADORN", "Traceback")) and not l.startswith("ADORN NUMBERS"):
            print(l)
    print("ADORN %s: %s" % (pid, "ok" if r.returncode == 0 else "FAILED (exit %d)" % r.returncode))
    return r.returncode == 0


FAN_METALS = ("steel", "blacksteel", "gold")      # (rigid plate meshes; not leather, rivets, gems or the shadow proxy)


def fan_fill(pid, gltf=None):
    """Fill the export's triangle fans (n-gon plates) with rings, on every plate mesh and LOD of the piece (fan_fill.py).
    Idempotent: a filled fan has no sliver fan left, so running it again finds nothing."""
    gltf = gltf or os.path.join(ROOT, "godot", "art", "armor", pid + ".gltf")
    meshes = [m["name"] for m in json.load(open(gltf, encoding="utf-8"))["meshes"]]
    ok = True
    for name in meshes:
        if name.rsplit(".", 1)[-1] not in FAN_METALS:
            continue
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "armor", "fan_fill.py"), gltf, name],
                           cwd=ROOT, capture_output=True, text=True)
        out = [l for l in r.stdout.splitlines() if not l.startswith(("  pole", "written"))]
        print("FANFILL " + (out[-1] if out else name) + ("" if r.returncode == 0 else " FAILED: " + r.stderr.strip()[-200:]))
        ok = ok and r.returncode == 0
    return ok


def build(pid, src):
    pj = os.path.join(ROOT, "godot", "art", "armor", "src", pid, "piece.json")
    piece = json.load(open(pj, encoding="utf-8"))
    if piece.get("base"):
        return adorn(pid) and fan_fill(pid)       # (no Blender: the base's built shell, copied)
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
        if ok and any(not (a["kind"] == "row" and a.get("mesh", "rivet") == "rivet") for a in piece.get("adorn", [])):
            ok = adorn(pid, post=True)
        if ok:
            ok = fan_fill(pid)      # (last: after the LODs and the adorn meshes are in the file)
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
        # (bases first: a variant copies its base's built shell)
        ids.sort(key=lambda i: "base" in json.load(open(os.path.join(ROOT, "godot", "art", "armor", "src", i, "piece.json"), encoding="utf-8")))
    if not os.path.exists(os.path.join(ROOT, "godot", "art", "armor", "trim_strip.json")):
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "armor", "trim_strip.py")], check=True)
    bad = [p for p in ids if not build(p, src)]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
