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
    with open(os.path.join(PUB, "publish.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"published {out['source']} -> godot/art/people/body_p1 ({len(out['files'])} files)")


def godot_import():
    if subprocess.call([sys.executable, TURN, "take", "godot", "body-p1: import", "--wait", "90"]) != 0:
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
