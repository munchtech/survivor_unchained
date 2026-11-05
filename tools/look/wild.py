"""The wild kit's one command (L1 C3a: LOOK_BIBLE rules 9 and 10; docs/design/look/TEXTURE_AUTHORING.md's contract).

    python tools/look/wild.py spruce|alder|rocks|all [--no-mesh] [--no-caps]

Per kind: (1) its generator in Blender (the blender turn taken and given back) builds the game's files in place,
godot/art/world/flora/ (spruce_a-c.gltf: tools/assets/env_trees.py's tiers; alder_a-c.gltf: its leaf clusters; boulder, fieldrock, cliff, pebbles,
stepping .gltf: tools/assets/env_rocks.py's planes) with uvs laid by the generator, and the painter's sheet
(godot/art/world/painted/_src/<kind>_sheet.glb: every size or variant once, materials named by class);
(2) tools/look/bake_forms.py prop SHEET --keep-uv SIZE --class-mat 1 bakes the form maps on those uvs;
(3) tools/look/paint_core.py paints them (arm A, each class's paint.albedo from godot/data/look/materials.json) and
checks them; (4) the albedo goes to the atlas the game files name (flora/spruce_atlas.png, flora/rock_atlas.png);
(5) the trees get their stump caps again (tools/assets/tree_caps.py). Outputs and their numbers:
godot/art/world/painted/<kind>/ (paint.json, the maps). Deterministic: the same sources give the same files.
--no-mesh repaints only (after a colour change in materials.json).
"""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
BLENDER = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
PAINTED = os.path.join(ROOT, "godot", "art", "world", "painted")
FLORA = os.path.join(ROOT, "godot", "art", "world", "flora")
KINDS = {
    "spruce": dict(gen=["tools/assets/env_trees.py", "mesh", "--species", "spruce"], size=2048, atlas="spruce_atlas.png", caps="spruce"),
    "alder": dict(gen=["tools/assets/env_trees.py", "mesh", "--species", "alder"], size=2048, atlas="alder_atlas.png", caps="alder"),
    "rocks": dict(gen=["tools/assets/env_rocks.py", "mesh", "--form", "planes"], size=2048, atlas="rock_atlas.png", caps=None),
}


def turn(*a): subprocess.run([sys.executable, os.path.join(ROOT, "tools", "turn.py"), *a], check=True, cwd=ROOT)


def blender(args, job):
    turn("take", "blender", f"L1 C3a: {job}", "--wait", "90")
    try:
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", *args], cwd=ROOT, capture_output=True, text=True)
    finally:
        turn("give", "blender")
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-4000:] + r.stderr[-3000:]); raise SystemExit(f"blender failed: {job}")
    return r.stdout


def build(kind, mesh=True, caps=True):
    k = KINDS[kind]
    t0 = time.time()
    if mesh:
        g = k["gen"]
        at = os.path.join(FLORA, k["atlas"])
        if not os.path.exists(at):  # (the game files name the atlas: a grey stand-in until the first paint)
            from PIL import Image
            Image.new("RGB", (64, 64), (128, 128, 128)).save(at)
        out = blender([os.path.join(ROOT, g[0]), "--", *g[1:]], f"{kind} mesh")
        for line in out.splitlines():
            if line.startswith("REPORT") or "tris" in line or "px/m" in line: print(" ", line)
    sheet = os.path.join(PAINTED, "_src", f"{kind}_sheet.glb")
    forms = os.path.join(PAINTED, "_forms", kind)
    shutil.rmtree(forms, ignore_errors=True); os.makedirs(forms)
    blender([os.path.join(HERE, "bake_forms.py"), "--", "prop", sheet, forms, "--asset", kind, "--node", "lod0",
             "--keep-uv", str(k["size"]), "--class-mat", "1"], f"{kind} forms")
    import paint_core
    out = os.path.join(PAINTED, kind)
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    paint_core.paint(forms, out, "A", None, "albedo")
    ok, lines = paint_core.check(out)
    from PIL import Image
    Image.open(os.path.join(out, "albedo.png")).convert("RGB").save(os.path.join(FLORA, k["atlas"]))
    if caps and k["caps"]:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "assets", "tree_caps.py"), k["caps"]], check=True, cwd=ROOT)
    print(f"{kind}: {'PASS' if ok else 'FAIL'} in {time.time() - t0:.0f} s")
    for ln in lines: print("  ", ln)
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    which = [x for x in a if not x.startswith("--")] or ["all"]
    kinds = list(KINDS) if which == ["all"] else which
    ok = all([build(kd, "--no-mesh" not in a, "--no-caps" not in a) for kd in kinds])
    sys.exit(0 if ok else 1)
