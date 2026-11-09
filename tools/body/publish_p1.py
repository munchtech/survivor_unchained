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
# (skin_pieces.py, a build's spec "pieces": A's skin-tight pieces carried onto B, P1Body.Piece; a build without them
# leaves the published ones as they were, said)
OPTIONAL = ("pieces.glb", "pieces.json")
GLBS = ("body.glb", "play.glb", "pieces.glb")
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


def body_laws(src, out):
    """P1 R1 sliders: what a body built from a ref body (build_topo target_joints_ref: a slider variant on her_b) needs at
    runtime of that change; none of it exists on the ref body itself (her_b: absent = no change).
      rig.json "hand_clear"     tools/body/hand_clear.py (rig_drive.hand_clear, P1Rig.HandClear): the arm opened by
                                the thigh surface's change, by the hand's proximity.
      publish.json "carry"      head_move_m: the build's rigid move of the baked head (build.json; the neck sliders'
                                head_move + the ground): P1Body.Rebind lays her hair and head pieces (A-skinned) by it,
                                HeadTurn/GazeCarry/eyes pivots and the hair's collision balls ride it;
                                ref_move_m {bone: [dx, dy, dz]}: each joint's rest move against the ref body's
                                (stage/close_skeleton.json vs ref_skeleton.json, over 0.01 mm): A-space points laid
                                on a B bone (pivots, balls) ride their bone's move (P1Body.OnB)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hand_clear
    hc = hand_clear.build(src)
    if hc:
        rp = os.path.join(PUB, "rig.json")
        rig = json.load(open(rp))
        rig["hand_clear"] = hc
        with open(rp, "w") as f:
            json.dump(rig, f, indent=1)
        out["files"]["rig.json"] = sha1(rp)
        out["laws"] = {"hand_clear": {s: hc["sides"][s]["_dr_max_mm"] for s in hc["sides"]}}
        print(f"publish_p1: rig.json hand_clear added (dr max mm {out['laws']['hand_clear']})")
    carry = {}
    bj = os.path.join(src, "build.json")
    if os.path.exists(bj):
        hm = json.load(open(bj)).get("head_move_m")
        if hm and max(abs(float(x)) for x in hm) > 0:
            carry["head_move_m"] = [float(x) for x in hm]
    sb, sr = (os.path.join(src, "stage", f) for f in ("close_skeleton.json", "ref_skeleton.json"))
    if os.path.exists(sb) and os.path.exists(sr):
        a, b = json.load(open(sb)), json.load(open(sr))
        if a["names"] == b["names"]:
            mv = {}
            for n, wa, wb in zip(a["names"], a["worlds"], b["worlds"]):
                d = [float(wa[k][3]) - float(wb[k][3]) for k in range(3)]
                if max(abs(x) for x in d) > 1e-5:
                    mv[n] = [round(x, 6) for x in d]
            if mv:
                carry["ref_move_m"] = mv
    if carry:
        out["carry"] = carry
        print(f"publish_p1: carry head_move_m {carry.get('head_move_m')}, ref_move_m {len(carry.get('ref_move_m', {}))} bones")


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
    body_laws(src, out)
    for f in OPTIONAL:
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(PUB, f))
            out["files"][f] = sha1(os.path.join(PUB, f))
        elif os.path.exists(os.path.join(PUB, f)):
            print(f"publish_p1: {src} has no {f}; the published one is an earlier build's")
    maps = os.path.join(src, "maps")
    bake = os.path.join(maps, "bake.json")
    if os.path.exists(bake) and json.load(open(bake)).get("gates", {}).get("pass"):
        for f in sorted(os.listdir(maps)):
            shutil.copy2(os.path.join(maps, f), os.path.join(PUB, f))
            out["files"][f] = sha1(os.path.join(PUB, f))
    else:
        out["maps"] = "not copied (no passing bake.json in the build)"
        # (B's own cavity map (topo_bake cavity_keep: its own AO about her armpits, P1 R1 round 33) is this build's surface,
        # not the carry the gates judge (the albedo's dE, the normal map's tangent frames): published with the glbs)
        for f in ("cavity.png",):
            if os.path.exists(os.path.join(maps, f)):
                shutil.copy2(os.path.join(maps, f), os.path.join(PUB, f))
                out["files"][f] = sha1(os.path.join(PUB, f))
    bj = os.path.join(src, "build.json")
    if os.path.exists(bj):
        out["spec"] = json.load(open(bj)).get("spec")
        # the spec's "skin" (the placeholder skin's shader settings for this body, not a tool's number): P1Body.ApplySkin reads it
        sp = os.path.join(ROOT, out["spec"]) if out["spec"] else None
        if sp and os.path.exists(sp):
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from sliders import load_spec          # (a variant spec's "base": the skin it inherits)
            if load_spec(sp).get("skin"):
                out["skin"] = load_spec(sp)["skin"]
    params = import_params()
    out["import"] = {"from": "godot/art/people/heroine.glb.import", "params": params, "changed": {}}
    for f in (g for g in GLBS if g in out["files"]):
        ch = write_import(os.path.join(PUB, f + ".import"), params)
        if ch:
            out["import"]["changed"][f] = ch
    with open(os.path.join(PUB, "publish.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"published {out['source']} -> {os.path.relpath(PUB, ROOT)} ({len(out['files'])} files)")


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


VAR = os.path.join(ROOT, "godot", "art", "people", "body_p1_var")
# (the gate body's maps and the freckles: a variant whose own bake did not pass takes them from the gate's folder, read
# only: the same UVs on the same topology)
MAPS_FALLBACK = ("albedo.png", "normal.png", "roughness.png", "ao.png", "curvature.png", "form_normal.png", "thickness.png",
                 "freckles.png", "region_id.png", "cavity.png", "bake.json")
# (baked on the build's own surface: from another shape they are that shape's, never this body's)
SHAPE_MAPS = ("normal.png", "ao.png", "curvature.png", "form_normal.png", "cavity.png", "thickness.png")


def publish_var(src, name):
    """P1 R1 sliders: --dest NAME publishes to godot/art/people/body_p1_var/NAME/ (git-ignored, pictures only: the game
    loads it with --p1-dir res://art/people/body_p1_var/NAME/); the gate body's folder is never written."""
    global PUB
    gate = PUB
    PUB = os.path.join(VAR, name)
    os.makedirs(PUB, exist_ok=True)
    publish(src)
    pj = os.path.join(PUB, "publish.json")
    with open(pj) as f:
        out = json.load(f)
    # (P1 R1 sliders round 5: a map this publish did not copy from the build is the gate body's, overwritten each time,
    # so a stale earlier copy never passes for the variant's own; the shape maps (baked on a surface) said LOUDLY: on
    # another shape they shade that shape's folds onto this one (bust_down round 4: base B's underbust line))
    fell = [f for f in MAPS_FALLBACK if f not in out["files"] and os.path.exists(os.path.join(gate, f))]
    for f in fell:
        shutil.copy2(os.path.join(gate, f), os.path.join(PUB, f))
        print(f"publish_p1: {name}: {f} from the gate body's folder")
    shape = [f for f in fell if f in SHAPE_MAPS]
    out["maps_own"] = not shape
    if fell:
        out["maps_fallback"] = {"from": os.path.relpath(gate, ROOT).replace("\\", "/"), "files": fell, "shape_maps_from_another_shape": shape,
                                "why": out.get("maps", "")}
    if shape:
        bar = "!" * 100
        print(bar, flush=True)
        print(f"publish_p1: {name}: WARNING: its own bake did not pass; SHAPE MAPS FROM THE GATE BODY'S SHAPE: {', '.join(shape)}", flush=True)
        print("  (pictures shot on this variant carry the gate body's folds and relief)", flush=True)
        print(bar, flush=True)
    with open(pj, "w") as f:
        json.dump(out, f, indent=1)
    PUB = gate


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dest = None
    if "--dest" in sys.argv:
        dest = sys.argv[sys.argv.index("--dest") + 1]
        args.remove(dest)
    if len(args) != 1:
        raise SystemExit(__doc__)
    if dest:
        publish_var(os.path.abspath(args[0]), dest)
    else:
        publish(os.path.abspath(args[0]))
    if "--import" in sys.argv:
        godot_import()
