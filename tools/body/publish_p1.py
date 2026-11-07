"""Publish a P1 build into the game (P1 F): B behind the --body p1 flag (godot/src/Actors/P1Body.cs).

    python tools/body/publish_p1.py <build_out> [--import]

Copies <build_out>/{body.glb, play.glb, rig.json, play_rig.json} and its baked maps (<build_out>/maps/*, the bake
stage's own, when its gates passed: bake.json "gates.pass") into godot/art/people/body_p1/, and writes
body_p1/publish.json (the source build, each file's sha1, the build's spec). Re-runnable: every run copies the
build's current outputs, so a revised build (the hip, the correctives) is one command away; nothing in body_p1/ is
edited by hand. --import then takes a Godot turn (tools/turn.py), runs Godot's headless import and gives it back.

Materials: the maps ride IN the glbs (build_topo's bake stage, glbwrite.attach_maps: the body material's
baseColorTexture = albedo.png, normalTexture = normal.png); the game binds nothing of its own. Derivation: (a) the
game's need: People.Skin reads her paint (AlbedoTexture) and relief (NormalTexture) from the glb's source material
for A, so B through the same door needs no B-only binding code, and one file is what the game draws. Checked here:
the published body.glb's "Heroine" material must carry both textures, or the publish fails.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUB = os.path.join(ROOT, "godot", "art", "people", "body_p1")
FILES = ("body.glb", "play.glb", "rig.json", "play_rig.json")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TURN = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def glb_json(p):
    with open(p, "rb") as f:
        b = f.read(20)
        n = struct.unpack("<I", b[12:16])[0]
        return json.loads(f.read(n))


def body_material(p, node="Heroine"):
    g = glb_json(p)
    mi = next(n["mesh"] for n in g["nodes"] if n.get("name") == node and "mesh" in n)
    return g["materials"][g["meshes"][mi]["primitives"][0]["material"]]


# B's glbs import as A's does (godot/art/people/heroine.glb.import), read from that file, not set here: the mesh kept whole
# (no generated LODs: Godot's LOD at the Look and close cameras drew her outline as a polygon, the shoulder and outer
# breast sawtoothed) and uncompressed (16-bit normals and tangents), and the images she carries inside her mipmapped by
# the same post-import script (tools_scenes/import_mipmaps.gd: without it her 2K relief and paint were read texel by
# texel, the arm's and shoulder's relief streaked where A's same map reads smooth). P1 A round 14.
A_IMPORT = os.path.join(ROOT, "godot", "art", "people", "heroine.glb.import")
IMPORT_KEYS = ("meshes/ensure_tangents", "meshes/generate_lods", "meshes/create_shadow_meshes", "meshes/force_disable_compression",
               "import_script/path", "gltf/embedded_image_handling")


def import_params(a_import=A_IMPORT):
    """{key: value text} of A's glb import for IMPORT_KEYS."""
    out = {}
    for line in open(a_import, encoding="utf-8"):
        k, _, v = line.rstrip("\n").partition("=")
        if k in IMPORT_KEYS:
            out[k] = v
    missing = [k for k in IMPORT_KEYS if k not in out]
    if missing:
        raise SystemExit(f"publish_p1: {a_import} lacks {missing}")
    return out


def write_import(glb_import, params):
    """Set params in an existing <glb>.import's [params] (Godot keeps the rest); returns the keys changed."""
    if not os.path.exists(glb_import):
        return []  # first import: Godot writes the file; the next publish sets it
    lines = open(glb_import, encoding="utf-8").read().split("\n")
    changed = []
    for i, line in enumerate(lines):
        k, _, v = line.partition("=")
        if k in params and v != params[k]:
            lines[i] = f"{k}={params[k]}"
            changed.append(k)
    if changed:
        with open(glb_import, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
    return changed


def publish(src):
    for f in FILES:
        if not os.path.exists(os.path.join(src, f)):
            raise SystemExit(f"publish_p1: {src} has no {f}")
    for f in ("body.glb", "play.glb"):
        m = body_material(os.path.join(src, f))
        if "baseColorTexture" not in m.get("pbrMetallicRoughness", {}) or "normalTexture" not in m:
            raise SystemExit(f"publish_p1: {f}'s body material carries no maps (run the build's bake stage)")
    os.makedirs(PUB, exist_ok=True)
    out = {"source": os.path.relpath(src, ROOT).replace("\\", "/"), "files": {}}
    for f in FILES:
        shutil.copy2(os.path.join(src, f), os.path.join(PUB, f))
        out["files"][f] = sha1(os.path.join(PUB, f))
    maps = os.path.join(src, "maps")
    bake = os.path.join(maps, "bake.json")
    if os.path.exists(bake) and json.load(open(bake)).get("gates", {}).get("pass"):
        for f in sorted(os.listdir(maps)):
            shutil.copy2(os.path.join(maps, f), os.path.join(PUB, f))
            out["files"][f] = sha1(os.path.join(PUB, f))
    else:
        out["maps"] = "not copied (no passing bake.json in the build)"
    bj = os.path.join(src, "build.json")
    if os.path.exists(bj):
        out["spec"] = json.load(open(bj)).get("spec")
        # the spec's "skin" (the placeholder skin's shader settings for this body, not a tool's number): P1Body.ApplySkin reads it
        sp = os.path.join(ROOT, out["spec"]) if out["spec"] else None
        if sp and os.path.exists(sp) and json.load(open(sp)).get("skin"):
            out["skin"] = json.load(open(sp))["skin"]
    params = import_params()
    out["import"] = {"from": "godot/art/people/heroine.glb.import", "params": params, "changed": {}}
    for f in ("body.glb", "play.glb"):
        ch = write_import(os.path.join(PUB, f + ".import"), params)
        if ch:
            out["import"]["changed"][f] = ch
    with open(os.path.join(PUB, "publish.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"published {out['source']} -> godot/art/people/body_p1 ({len(out['files'])} files)")


def godot_import():
    # --stale-ok: this run IS the fix freshness asks for (the import of the glbs just published), so it must not be refused for them
    if subprocess.call([sys.executable, TURN, "take", "godot", "body-p1: import", "--wait", "90", "--stale-ok"]) != 0:
        raise SystemExit("publish_p1: no godot turn")
    try:
        r = subprocess.call([GODOT, "--headless", "--path", os.path.join(ROOT, "godot"), "--import"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
        print("godot import exit", r)
    finally:
        subprocess.call([sys.executable, TURN, "give", "godot", "body-p1: import"])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    publish(os.path.abspath(args[0]))
    if "--import" in sys.argv:
        godot_import()
