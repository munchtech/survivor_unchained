"""A base-body NPC holding its own props (World.NpcHeld) in the real game: the package staged from a rigged glb (a Marionette
workshop build on the current base body, e.g. generated/rnd/x18/w8/v1/npc.glb), its manifest's "held" naming a hand
lamp (left, carry lamp) and the smith's hammer (right, carry hand), read through --npc-overlay (nothing copied into
art/npc). Then the frames (the play camera and the close-up, before = the carry's Reach forced to 0, after = as built)
and the lamp's clearance to the body in mm (tools_scenes/FolkHold.cs + tools/anim/folkhold.py, idle and walk).

    python tools/npc/held_check.py OUT --glb GLB [--name x18_keeper_held] [--hair-colour #2a1c14] [--only shoot|measure]

The prop files' frame (NpcHeld): origin = the grip (where the fist closes), +Y out of the fist along the shaft (the
hammer's head; the lamp's hanging ring, the lamp below along -Y), +Z the face, drawn 1:1.
  hand lamp: art/props/keeper_lamp/keeper_lamp.glb (0.154 x 0.326 m), its grip the bail's top bar 0.092 above the ring;
    glass the keepers' violet, the iron's game-only mask colours dropped.
  hammer: art/weapons/smith_hammer.glb (0.397 m, shaft on +Y, head across X), its grip at its anchor_grip (0.07 up the
    shaft), turned a quarter about Y so the head's face is +Z.
Takes the godot turn (tools/turn.py) for the batch and gives it back.
"""
import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G = ROOT / "godot"
GODOT = os.environ.get("GODOT_EXE", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe")
TURN = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
LAMP, HAMMER = G / "art/props/keeper_lamp/keeper_lamp.glb", G / "art/weapons/smith_hammer.glb"
BASE = ["--quick", "warden", "--sex", "female", "--nohud", "--zone", "verge", "--facing", "0", "--seed", "1", "--time", "day", "--clock", "120"]
# (shot, --npc flags, extra args)
SHOTS = [("play", "", ["--seconds", "6"]), ("close", ":swap:chest", ["--close", "1", "--idle-after", "1", "--seconds", "8"]),
         ("play_walk", ":walk", ["--seconds", "6"])]


def glb_read(p):
    b = Path(p).read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    rest = b[20 + n:]
    return json.loads(b[20:20 + n]), rest[8:8 + struct.unpack("<I", rest[:4])[0]]


def glb_write(p, j, binary):
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_bytes(b"glTF" + struct.pack("<II", 2, 28 + len(js) + len(binary)) + struct.pack("<I", len(js)) + b"JSON" + js
                        + struct.pack("<I", len(binary)) + b"BIN\0" + binary)


def reframe(src, out, translation, rotation=(0, 0, 0, 1), edit=None):
    """The glb under one root node that moves its grip to the origin (and turns its face to +Z)."""
    j, binary = glb_read(src)
    if edit:
        edit(j)
    scene = j["scenes"][j.get("scene", 0)]
    j["nodes"].append({"name": "Held", "translation": list(translation), "rotation": list(rotation), "children": list(scene["nodes"])})
    scene["nodes"] = [len(j["nodes"]) - 1]
    glb_write(out, j, binary)


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lamp_edit(j):
    for m in j["meshes"]:
        for p in m["primitives"]:
            for k in ("COLOR_0", "COLOR_1"):
                p["attributes"].pop(k, None)
    violet = [lin(int("a77bff"[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    for mat in j["materials"]:
        if mat["name"] == "keeper_glass":
            mat["pbrMetallicRoughness"]["baseColorFactor"] = [*(c * 0.5 for c in violet), 1]
            mat["emissiveFactor"] = violet
        if mat["name"] == "keeper_iron":
            mat["pbrMetallicRoughness"].update(metallicFactor=0.6, roughnessFactor=0.6)


def stage(out, glb, name, hair):
    pk = out / "pkg"
    pk.mkdir(parents=True, exist_ok=True)
    body = pk / "body.glb"
    if not body.exists():
        try:
            os.link(glb, body)   # (a hard link: the 220 MB glb not copied; removing it leaves the source)
        except OSError:
            shutil.copyfile(glb, body)
    j, _ = glb_read(glb)
    joints = [j["nodes"][i].get("name", "") for i in j["skins"][0]["joints"]]
    acc = [j["accessors"][p["attributes"]["POSITION"]] for m in j["meshes"] for p in m["primitives"]]
    lo, hi = min(a["min"][1] for a in acc if "min" in a), max(a["max"][1] for a in acc if "max" in a)
    reframe(LAMP, pk / "props/hand_lamp.glb", (0, -0.092, 0), edit=lamp_edit)
    s = math.sqrt(0.5)
    reframe(HAMMER, pk / "props/hammer.glb", (0, -0.07, 0), (0, -s, 0, s))
    man = {"name": name, "sex": "female", "height": round(hi - lo, 4), "joints": len(joints), "baked": True, "body": "body.glb",
           "pieces": [], "from": str(Path(glb).resolve()).replace("\\", "/"), "hair": {"colour": hair},
           "held": {"handslot.l": {"file": "props/hand_lamp.glb", "carry": "lamp"},
                    "handslot.r": {"file": "props/hammer.glb", "carry": "hand"}}}
    (pk / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    return pk


def run(cmd, log, env=None):
    r = subprocess.run(cmd, cwd=G, capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL, env=env)
    Path(log).write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
    return r.returncode


def shoot(out, pk, name):
    shots = G / ".shots"
    ov = ["--npc-overlay", f"{name}={pk.as_posix()}"]
    for tag, flags in (("before", ":reach0"), ("after", "")):
        for shot, f, extra in SHOTS:
            if tag == "before" and shot == "play_walk":
                continue
            t = f"held_{tag}_{shot}"
            for x in shots.glob(f"{t}*.png"):
                x.unlink()
            rc = run([GODOT, "--path", ".", "--fixed-fps", "60", "--resolution", "1920x1080", "--", *BASE, *ov, *extra,
                      "--npc", name + f + flags, "--npc-debug", "--shot", t], out / f"log_{tag}_{shot}.txt")
            got = sorted(x for x in shots.glob(f"{t}*.png") if re.fullmatch(rf"{t}(_\d+)?\.png", x.name))
            if got:
                shutil.move(str(got[0]), out / f"{tag}_{shot}.png")
            print(f"{tag} {shot}: {'ok' if got else f'MISSING (exit {rc})'}")


def measure(out, pk, name):
    for tag, reach in (("before", "0"), ("after", None)):
        env = dict(os.environ)
        env.pop("FOLKHOLD_REACH", None)
        if reach:
            env["FOLKHOLD_REACH"] = reach
        for clip in ("Idle", "Walk"):
            dump = out / f"hold_{tag}_{clip}.json"
            rc = run([GODOT, "--headless", "--path", ".", "-s", "res://tools_scenes/folk_hold.gd", "--", str(dump), f"pkg.{name}", clip, "12",
                      "--npc-overlay", f"{name}={pk.as_posix()}"], out / f"log_hold_{tag}_{clip}.txt", env)
            if dump.exists():
                r = subprocess.run([sys.executable, str(ROOT / "tools/anim/folkhold.py"), str(dump)], capture_output=True, text=True)
                (out / f"clear_{tag}_{clip}.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
                print(f"clearance {tag} {clip}: {out / f'clear_{tag}_{clip}.txt'}")
            else:
                print(f"clearance {tag} {clip}: NO DUMP (exit {rc})")


def sheets(out):
    from PIL import Image, ImageDraw
    for shot in ("play", "close"):
        a, b = out / f"before_{shot}.png", out / f"after_{shot}.png"
        if not (a.exists() and b.exists()):
            continue
        A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
        s = Image.new("RGB", (A.width + B.width + 8, A.height + 28), (16, 16, 16))
        d = ImageDraw.Draw(s)
        s.paste(A, (0, 28))
        s.paste(B, (A.width + 8, 28))
        d.text((8, 8), f"BEFORE (lamp carry Reach 0) - {shot} camera, 1:1", fill=(230, 230, 230))
        d.text((A.width + 16, 8), f"AFTER (as built) - {shot} camera, 1:1", fill=(230, 230, 230))
        s.save(out / f"sheet_{shot}.png")
        print(f"sheet: {out / f'sheet_{shot}.png'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--glb", required=True)
    ap.add_argument("--name", default="x18_keeper_held")
    ap.add_argument("--hair-colour", default="#2a1c14")
    ap.add_argument("--only", choices=["shoot", "measure"])
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pk = stage(out, Path(a.glb), a.name, a.hair_colour)
    print(f"staged {pk}")
    who = f"npc held: {a.name}"
    if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", "30"]).returncode:
        sys.exit("no godot turn")
    try:
        if a.only != "measure":
            shoot(out, pk, a.name)
        if a.only != "shoot":
            measure(out, pk, a.name)
    finally:
        subprocess.run([sys.executable, TURN, "give", "godot", who])
    sheets(out)


if __name__ == "__main__":
    main()
