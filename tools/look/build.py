"""The world-side build (L1 B3 round 2): one command per painted asset, from its source mesh to the painted maps.

    python tools/look/build.py ASSET|all [--twice]

Reads godot/data/look/painted.json. Per asset: bake_forms.py in Blender (the blender turn taken and given back) into the
git-ignored godot/art/world/painted/_forms/<asset>/, paint_core (arm A, albedo src "albedo") into godot/art/world/painted/<asset>/
(albedo.png, normal.png, rough.png, paint.json, mesh.glb copied for props), paint_core.check() and the brush px at play; then
godot/art/world/painted/maps.json (B3Maps's manifest, res:// paths) for every built asset. --twice builds into two temp dirs and
reports whether every output file is byte-identical (timing.json excluded); it writes nothing else.
"""
import json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
BLENDER = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
PAINTED = os.path.join(ROOT, "godot", "art", "world", "painted")
CFG = json.load(open(os.path.join(ROOT, "godot", "data", "look", "painted.json"), encoding="utf-8"))["assets"]


def turn(*a): subprocess.run([sys.executable, os.path.join(ROOT, "tools", "turn.py"), *a], check=True, cwd=ROOT)


def bake(asset, forms):
    c = CFG[asset]
    shutil.rmtree(forms, ignore_errors=True); os.makedirs(forms)
    cmd = [BLENDER, "-b", "--factory-startup", "-P", os.path.join(HERE, "bake_forms.py"), "--"]
    if c["kind"] == "prop":
        cmd += ["prop", os.path.join(ROOT, c["mesh"]), forms, "--asset", asset, "--node", c["node"]]
        if "variant" in c: cmd += ["--variant", str(c["variant"])]
    else:
        cmd += ["setts", forms, "--tile", str(c["tile"])]
    # (--stale-ok: the bake reads only the asset's own mesh, never her art, shaders or clips)
    turn("take", "blender", f"look-l1: B3 build {asset}", "--stale-ok")
    t = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    finally:
        turn("give", "blender")
    if r.returncode != 0 or not os.path.exists(os.path.join(forms, "forms.npz")):
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:]); raise SystemExit(f"bake_forms failed for {asset}")
    return time.time() - t


def paint(asset, forms, out):
    import paint_core
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    t = time.time()
    paint_core.paint(forms, out, "A", None, "albedo")
    if CFG[asset]["kind"] == "prop": shutil.copyfile(os.path.join(forms, "mesh.glb"), os.path.join(out, "mesh.glb"))
    return time.time() - t


def check(out):
    import paint_core
    ok, lines = paint_core.check(out)
    P = json.load(open(os.path.join(out, "paint.json")))
    lines += ["brush px at play: " + ", ".join(f"{n} {cm / 100 * paint_core.PLAY_PX_PER_M:.1f}" for n, cm in P["brush_cm"].items())
              + f" (cm: {P['brush_cm']})"]
    return ok, lines


def build(asset, forms=None, out=None):
    forms = forms or os.path.join(PAINTED, "_forms", asset); out = out or os.path.join(PAINTED, asset)
    sb = bake(asset, forms); sp = paint(asset, forms, out)
    ok, lines = check(out)
    print(f"== {asset}: blender {sb:.0f} s, paint {sp:.0f} s, check {'PASS' if ok else 'FAIL'}")
    print("\n".join("   " + l for l in lines))
    return ok


def maps_json():
    items = []
    for a, c in CFG.items():
        if not os.path.exists(os.path.join(PAINTED, a, "paint.json")): continue
        names = json.load(open(os.path.join(PAINTED, "_forms", a, "forms.json")))["classes"]
        res = f"res://art/world/painted/{a}/"
        e = dict(node=c["stage"]["node"], maps={n: {k: res + k + ".png" for k in ("albedo", "normal", "rough")} for n in names})
        if "near" in c["stage"]: e.update(at=c["stage"]["at"], near=c["stage"]["near"])
        if c["kind"] == "prop": e["mesh"] = res + "mesh.glb"
        else: e.update(tile=c["stage"]["tile"], name=c["stage"]["name"])
        items.append(e)
    json.dump({"items": items}, open(os.path.join(PAINTED, "maps.json"), "w", newline="\n"), indent=1)
    print(f"maps.json: {len(items)} items")


def files(d):
    return {os.path.relpath(os.path.join(r, f), d).replace(os.sep, "/"): os.path.join(r, f)
            for r, _, fs in os.walk(d) for f in fs if f != "timing.json"}


def twice(asset):
    base = os.path.join(PAINTED, "_forms", "_twice", asset)
    shutil.rmtree(base, ignore_errors=True)
    for i in (1, 2): build(asset, os.path.join(base, str(i), "forms"), os.path.join(base, str(i), "out"))
    same = True
    for sub in ("forms", "out"):
        a, b = files(os.path.join(base, "1", sub)), files(os.path.join(base, "2", sub))
        for k in sorted(set(a) | set(b)):
            eq = k in a and k in b and open(a[k], "rb").read() == open(b[k], "rb").read()
            same &= eq
            print(f"   {'same ' if eq else 'DIFF '}{sub}/{k}")
    print(f"== {asset}: two runs {'byte-identical' if same else 'DIFFER'}")
    return same


if __name__ == "__main__":
    a = sys.argv[1:]; tw = "--twice" in a
    a = [x for x in a if x != "--twice"]
    names = list(CFG) if a[0] == "all" else [a[0]]
    res = [(twice if tw else build)(n) for n in names]
    if not tw: maps_json()
    sys.exit(0 if all(res) else 1)
